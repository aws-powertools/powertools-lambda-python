package main

import (
	"context"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/signal"
	"sort"
	"sync"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/lambda"
	"github.com/aws/aws-sdk-go-v2/service/lambda/types"
	"golang.org/x/exp/slices"
	"golang.org/x/sync/errgroup"
)

type LayerInfo struct {
	Name         string
	Description  string
	Architecture types.Architecture

	LayerContentOnce sync.Once
	LayerContent     []byte
}

// canonicalLayers are the layers that we want to keep in sync across all regions
var canonicalLayers = []LayerInfo{
	{
		Name:         "AWSLambdaPowertoolsPythonV2",
		Description:  "Lambda Powertools for Python [x86_64] with extra dependencies version bump",
		Architecture: types.ArchitectureX8664,
	},
	{
		Name:         "AWSLambdaPowertoolsPythonV2-Arm64",
		Description:  "Lambda Powertools for Python [arm64] with extra dependencies version bump",
		Architecture: types.ArchitectureArm64,
	},
}

// regions are the regions that we want to keep in sync
var regions = []string{
	"af-south-1",
	"ap-east-1",
	"ap-northeast-1",
	"ap-northeast-2",
	"ap-northeast-3",
	"ap-south-1",
	"ap-south-2",
	"ap-southeast-1",
	"ap-southeast-2",
	"ap-southeast-3",
	"ap-southeast-4",
	"ca-central-1",
	"eu-central-1",
	"eu-central-2",
	"eu-north-1",
	"eu-south-1",
	"eu-south-2",
	"eu-west-1",
	"eu-west-2",
	"eu-west-3",
	"me-central-1",
	"me-south-1",
	"sa-east-1",
	"us-east-1",
	"us-east-2",
	"us-west-1",
	"us-west-2",
}

var singleArchitectureRegions = []string{
	"ap-south-2",
	"ap-southeast-4",
	"eu-central-2",
	"eu-south-2",
	"me-central-1",
}

// getLayerVersion returns the latest version of a layer in a region
func getLayerVersion(ctx context.Context, layerName string, region string) (int64, error) {
	cfg, err := config.LoadDefaultConfig(ctx, config.WithRegion(region))
	if err != nil {
		return 0, err
	}

	lambdaSvc := lambda.NewFromConfig(cfg)

	layerVersionsResult, err := lambdaSvc.ListLayerVersions(ctx, &lambda.ListLayerVersionsInput{
		LayerName: aws.String(layerName),
		MaxItems:  aws.Int32(1),
	})
	if err != nil {
		return 0, err
	}

	if len(layerVersionsResult.LayerVersions) == 0 {
		return 0, fmt.Errorf("no layer meets the search criteria %s - %s", layerName, region)
	}
	return layerVersionsResult.LayerVersions[0].Version, nil
}

// getGreatestVersion returns the greatest version of a layer across all regions
func getGreatestVersion(ctx context.Context) (int64, error) {
	var versions []int64

	g, ctx := errgroup.WithContext(ctx)

	for idx := range canonicalLayers {
		layer := &canonicalLayers[idx]

		for _, region := range regions {
			// Ignore regions that are excluded
			if layer.Architecture == types.ArchitectureArm64 && slices.Contains(singleArchitectureRegions, region) {
				continue
			}

			layerName := layer.Name
			ctx := ctx
			region := region

			g.Go(func() error {
				version, err := getLayerVersion(ctx, layerName, region)
				if err != nil {
					return err
				}

				log.Printf("[%s] %s -> %d", layerName, region, version)

				versions = append(versions, version)
				return nil
			})
		}
	}

	if err := g.Wait(); err != nil {
		return 0, err
	}

	// Find the maximum version by reverse sorting the versions array
	sort.Slice(versions, func(i, j int) bool { return versions[i] > versions[j] })
	return versions[0], nil
}

// balanceRegionToVersion creates a new layer version in a region with the same contents as the canonical layer, until it matches the maxVersion
func balanceRegionToVersion(ctx context.Context, region string, layer *LayerInfo, maxVersion int64) error {
	currentLayerVersion, err := getLayerVersion(ctx, layer.Name, region)
	if err != nil {
		return fmt.Errorf("error getting layer version: %w", err)
	}

	cfg, err := config.LoadDefaultConfig(ctx, config.WithRegion(region))
	if err != nil {
		return err
	}

	lambdaSvc := lambda.NewFromConfig(cfg)

	for i := currentLayerVersion; i < maxVersion; i++ {
		log.Printf("[%s] Bumping %s to version %d (max %d)", layer.Name, region, i, maxVersion)

		payload, err := downloadCanonicalLayerZip(ctx, layer)
		if err != nil {
			return fmt.Errorf("error downloading canonical zip: %w", err)
		}

		var layerVersionResponse *lambda.PublishLayerVersionOutput

		if slices.Contains(singleArchitectureRegions, region) {
			layerVersionResponse, err = lambdaSvc.PublishLayerVersion(ctx, &lambda.PublishLayerVersionInput{
				Content: &types.LayerVersionContentInput{
					ZipFile: payload,
				},
				LayerName:          aws.String(layer.Name),
				CompatibleRuntimes: []types.Runtime{types.RuntimePython37, types.RuntimePython38, types.RuntimePython39},
				Description:        aws.String(layer.Description),
				LicenseInfo:        aws.String("MIT-0"),
			})
		} else {
			layerVersionResponse, err = lambdaSvc.PublishLayerVersion(ctx, &lambda.PublishLayerVersionInput{
				Content: &types.LayerVersionContentInput{
					ZipFile: payload,
				},
				LayerName:               aws.String(layer.Name),
				CompatibleArchitectures: []types.Architecture{layer.Architecture},
				CompatibleRuntimes:      []types.Runtime{types.RuntimePython37, types.RuntimePython38, types.RuntimePython39},
				Description:             aws.String(layer.Description),
				LicenseInfo:             aws.String("MIT-0"),
			})
		}
		if err != nil {
			return fmt.Errorf("error publishing layer version: %w", err)
		}

		_, err = lambdaSvc.AddLayerVersionPermission(ctx, &lambda.AddLayerVersionPermissionInput{
			Action:        aws.String("lambda:GetLayerVersion"),
			LayerName:     aws.String(layer.Name),
			Principal:     aws.String("*"),
			StatementId:   aws.String("PublicLayerAccess"),
			VersionNumber: layerVersionResponse.Version,
		})
		if err != nil {
			return fmt.Errorf("error making layer public: %w", err)
		}
	}

	return nil
}

// balanceRegions creates new layer versions in all regions with the same contents as the canonical layer, until they match the maxVersion
func balanceRegions(ctx context.Context, maxVersion int64) error {
	g, ctx := errgroup.WithContext(ctx)

	for idx := range canonicalLayers {
		layer := &canonicalLayers[idx]

		for _, region := range regions {
			// Ignore regions that are excluded
			if layer.Architecture == types.ArchitectureArm64 && slices.Contains(singleArchitectureRegions, region) {
				continue
			}

			ctx := ctx
			region := region
			layer := layer
			version := maxVersion

			g.Go(func() error {
				return balanceRegionToVersion(ctx, region, layer, version)
			})
		}
	}

	if err := g.Wait(); err != nil {
		return err
	}

	return nil
}

// downloadCanonicalLayerZip downloads the canonical layer zip file that will be used to bump the versions later
func downloadCanonicalLayerZip(ctx context.Context, layer *LayerInfo) ([]byte, error) {
	var innerErr error

	layer.LayerContentOnce.Do(func() {
		// We use eu-central-1 as the canonical region to download the Layer from
		cfg, err := config.LoadDefaultConfig(ctx, config.WithRegion("eu-central-1"))
		if err != nil {
			innerErr = err
		}

		lambdaSvc := lambda.NewFromConfig(cfg)

		// Gets the latest version of the layer
		version, err := getLayerVersion(ctx, layer.Name, "eu-central-1")
		if err != nil {
			innerErr = fmt.Errorf("error getting eu-central-1 layer version: %w", err)
		}

		// Gets the Layer content URL from S3
		getLayerVersionResult, err := lambdaSvc.GetLayerVersion(ctx, &lambda.GetLayerVersionInput{
			LayerName:     aws.String(layer.Name),
			VersionNumber: version,
		})
		if err != nil {
			innerErr = fmt.Errorf("error getting eu-central-1 layer download URL: %w", err)
		}

		s3LayerUrl := getLayerVersionResult.Content.Location
		log.Printf("[%s] Downloading Layer from %s", layer.Name, *s3LayerUrl)

		resp, err := http.Get(*s3LayerUrl)
		if err != nil {
			innerErr = err
		}
		defer resp.Body.Close()

		body, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			innerErr = err
		}

		layer.LayerContent = body
	})

	return layer.LayerContent, innerErr
}

func main() {
	ctx := context.Background()

	// Cancel everything if interrupted
	ctx, cancel := context.WithCancel(ctx)
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt)
	defer func() {
		signal.Stop(c)
		cancel()
	}()
	go func() {
		select {
		case <-c:
			cancel()
		case <-ctx.Done():
		}
	}()

	// Find the greatest layer version across all regions
	greatestVersion, err := getGreatestVersion(ctx)
	if err != nil {
		cancel()
		log.Printf("error getting layer version: %s", err)
		os.Exit(1)
	}
	log.Printf("Greatest version is %d. Bumping all versions...", greatestVersion)

	// Elevate all regions to the greatest layer version found
	err = balanceRegions(ctx, greatestVersion)
	if err != nil {
		cancel()
		log.Printf("error balancing regions: %s", err)
		os.Exit(1)
	}

	log.Printf("DONE! All layers should be version %d", greatestVersion)
}
