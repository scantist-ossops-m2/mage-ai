import { gradientBackground } from '../../../styles/mixins';
import scrollbars from '@mana/styles/scrollbars';
import styled from 'styled-components';

export const ContainerStyled = styled.div`
  .header {
    ${gradientBackground('0deg', '#0000004D', '#0000004D', 0, 100, 'graylo')}
    backdrop-filter: blur(20px);
    left: 0;
    overflow: hidden;
    position: sticky;
    top: 0;
    z-index: 1;
  }

  .table {
    ${scrollbars}
    border-bottom: 1px solid var(--borders-color-base-default);
    border-left: 1px solid var(--borders-color-base-default);
    border-right: 1px solid var(--borders-color-base-default);
    border-spacing: 0;
    border-top: 1px solid var(--borders-color-base-default);
    display: inline-block;

    .tr {
      .td.td-index-column {
        ${gradientBackground('0deg', '#0000004D', '#0000004D', 0, 100, 'graylo')}
        backdrop-filter: blur(20px);
        color: var(--fonts-color-text-base);
        left: 0;
        position: sticky;
        z-index: 2;
      }

    .th {
      color: var(--fonts-color-text-base);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;

      &.th-monospace {
        font-family: var(--fonts-family-monospace-regular);
      }
    }

    .th,
    .td {
      border-bottom: 1px solid var(--borders-color-base-default);
      border-right: 1px solid var(--borders-color-base-default);
      font-family: var(--fonts-family-base-regular);
      font-size: var(--fonts-size-sm);
      font-style: var(--fonts-style-base);
      font-weight: var(--fonts-weight-regular);
      line-height: var(--fonts-lineheight-sm);
      margin: 0;
      white-space: break-spaces;
      word-break: break-word;
    }

    .td {
      color: var(--fonts-color-text-secondary);

      &.td-monospace {
        font-family: var(--fonts-family-monospace-regular);
      }

      .td-list-item {
        padding: var(--padding-xs);
      }

      .json-object {
        ${scrollbars}
        overflow-x: auto;
        padding: 0;
      }
    }

    &.sticky {
      overflow: auto;
    }

    .header {
      overflow: hidden;
    }
  }
`;