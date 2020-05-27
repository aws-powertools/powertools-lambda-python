import React from 'react';
import styled from '@emotion/styled';
import { ReactComponent as AWSLogo } from '../../assets/aws-logo.svg';


const Wrapper = styled.div({
    display: 'flex',
    padding: '0 60px',
    height: '5vh'
});

const StyledAwsIcon = styled(AWSLogo)({
    width: '100%'
});

export default function Logo() {
    return (
        <Wrapper className="logo-container">
            <StyledAwsIcon/>
        </Wrapper>
    );
}
