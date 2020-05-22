import React from 'react';
import styled from '@emotion/styled';
import { ReactComponent as WALogo } from '../src/assets/wa-logo.svg';


const Wrapper = styled.div({
    display: 'flex'
});

const StyledWellArchitectedIcon = styled(WALogo)({
    height: '100%'
});

export default function Logo() {
    return (
        <Wrapper>
            <StyledWellArchitectedIcon/>
        </Wrapper>
    );
}
