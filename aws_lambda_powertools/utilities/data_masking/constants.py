# The string that replaces values that have been erased
DATA_MASKING_STRING: str = "*****"
# The maximum number of entries that can be retained in the local cryptographic materials cache
CACHE_CAPACITY: int = 100
# The maximum time (in seconds) that a cache entry may be kept in the cache
MAX_CACHE_AGE_SECONDS: float = 300.0
# Maximum number of messages which are allowed to be encrypted under a single cached data key
# Values can be [1 - 4294967296] (2 ** 32)
MAX_MESSAGES_ENCRYPTED: int = 4294967296
# Maximum number of bytes which are allowed to be encrypted under a single cached data key
# Values can be [1 - 9223372036854775807] (2 ** 63 - 1)
MAX_BYTES_ENCRYPTED: int = 9223372036854775807

ENCRYPTED_DATA_KEY_CTX_KEY = "aws-crypto-public-key"
