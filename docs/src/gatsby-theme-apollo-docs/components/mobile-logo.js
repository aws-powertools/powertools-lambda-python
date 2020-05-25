import React from 'react';
import styled from '@emotion/styled';

import { ReactComponent as Logo } from '../../assets/aws-logo.svg';

const Wrapper = styled.div({
    display: 'flex',
    height: '5vh'
});

const AwsMobileLogo = styled(Logo)({
    height: 'auto'
});

export function MobileLogo() {
    return (
        <Wrapper className="logo-container">
            <AwsMobileLogo />
        </Wrapper>
    );
}
