/**
 * The palette's accessibility claims, recomputed rather than trusted.
 *
 * `DESIGN.md` publishes a contrast ratio for every colour. Those ratios are the basis of
 * the accessibility claims in the thesis, and a number in a document nobody reopens is a
 * number that drifts from the value beside it. These tests recompute each one from the hex.
 */

import { describe, expect, it } from 'vitest';

import { SERIES_NEEDING_RELIEF, chart, chrome, series } from './tokens';
import type { Token } from './tokens';

const WHITE = '#ffffff';

/** WCAG 2.1 relative luminance. */
function luminance(hex: string): number {
  const channels = [1, 3, 5].map((i) => {
    const value = Number.parseInt(hex.slice(i, i + 2), 16) / 255;
    return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  }) as [number, number, number];
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function contrast(a: string, b: string): number {
  const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x) as [number, number];
  return (light + 0.05) / (dark + 0.05);
}

const everyToken: [string, Token][] = [
  ...Object.entries(chrome),
  ...Object.entries(series).map(([k, v]) => [`series-${k}`, v] as [string, Token]),
  ...Object.entries(chart).map(([k, v]) => [`chart-${k}`, v] as [string, Token]),
];

describe('the published contrast ratios', () => {
  it.each(everyToken)('%s matches what DESIGN.md claims', (_name, token) => {
    // Two decimal places is the precision the document publishes.
    expect(contrast(token.hex, WHITE)).toBeCloseTo(token.contrast, 1);
  });
});

describe('the relief-channel rule', () => {
  it('flags exactly the slots below the 3:1 mark floor', () => {
    // Below 3:1 a mark cannot carry meaning by colour alone, so the chart owes the reader
    // another channel — direct labels, or the table view.
    const flagged = Object.entries(series)
      .filter(([, token]) => token.needsReliefChannel)
      .map(([slot]) => Number(slot));
    expect(flagged).toEqual([...SERIES_NEEDING_RELIEF]);
  });

  it('flags a slot if and only if it is under 3:1', () => {
    for (const [slot, token] of Object.entries(series)) {
      const under = contrast(token.hex, WHITE) < 3;
      expect(Boolean(token.needsReliefChannel), `series-${slot}`).toBe(under);
    }
  });
});

describe('text', () => {
  it('primary and secondary clear 4.5:1', () => {
    expect(contrast(chrome.textPrimary.hex, WHITE)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(chrome.textSecondary.hex, WHITE)).toBeGreaterThanOrEqual(4.5);
  });

  it('primary clears 4.5:1 as a button label on white', () => {
    // White text on the chrome blue, which is why chrome blue is one step darker than
    // series-1. Unifying the two would break one gate or the other.
    expect(contrast(chrome.primary.hex, WHITE)).toBeGreaterThanOrEqual(4.5);
  });
});

describe('the series slots are distinct values', () => {
  it('no two slots share a hex', () => {
    const hexes = Object.values(series).map((token) => token.hex);
    expect(new Set(hexes).size).toBe(hexes.length);
  });

  it('series-other is not the disabled text colour', () => {
    // It was #9e9e9e — byte-identical to text-disabled, and indistinguishable from the
    // green slot under deuteranopia, so a class and the "Other" fold read as one mark.
    expect(series.other.hex).not.toBe(chrome.textDisabled.hex);
  });
});
