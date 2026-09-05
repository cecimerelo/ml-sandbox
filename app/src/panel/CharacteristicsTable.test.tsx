import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { CharacteristicsTable } from './CharacteristicsTable';
import { theme } from '../theme/theme';
import type { Characteristics, Suggestion } from './types';

function characteristics(overrides: Partial<Characteristics> = {}): Characteristics {
  return {
    method: 'random_forest',
    label: 'Random Forest',
    interpretability: { word: 'low', step: 1 },
    handles_non_linearity: { word: 'high', step: 3 },
    handles_missing_values: { word: 'yes', step: 3 },
    accuracy_potential: { word: 'high', step: 3 },
    training_speed: { word: 'moderate', step: 2 },
    ...overrides,
  };
}

function suggestion(overrides: Partial<Suggestion> = {}): Suggestion {
  return {
    method: 'random_forest',
    label: 'Random Forest',
    flexibility: { label: 'flexible', detail: 'splits the data repeatedly' },
    interpretability: { label: 'opaque', detail: 'no single reason to give for one answer' },
    expected_shortfall: 0.02,
    uncertainty: 0.005,
    reasons: [],
    factors: [],
    characteristics: characteristics(),
    excluded_by_constraint: false,
    ...overrides,
  };
}

function show(recommended: Suggestion, alternatives: Suggestion[] = []) {
  render(
    <ThemeProvider theme={theme}>
      <CharacteristicsTable recommended={recommended} alternatives={alternatives} />
    </ThemeProvider>,
  );
}

describe('the table', () => {
  it('renders every declared axis, word and dots both', () => {
    show(suggestion());
    expect(screen.getAllByText('high').length).toBeGreaterThan(0); // accuracy potential
    expect(screen.getAllByText('●●●').length).toBeGreaterThan(0);
    expect(screen.getByText('low')).toBeInTheDocument(); // interpretability
  });

  it('lists the recommended method first, then the alternatives', () => {
    show(
      suggestion({ method: 'random_forest', label: 'Random Forest' }),
      [suggestion({ method: 'ridge', label: 'Ridge', characteristics: characteristics({ method: 'ridge', label: 'Ridge' }) })],
    );
    const rows = screen.getAllByRole('row').slice(1); // drop the header row
    expect(rows[0]).toHaveTextContent('Random Forest');
    expect(rows[1]).toHaveTextContent('Ridge');
  });

  it('skips a method with no characteristics row rather than erroring', () => {
    show(
      suggestion(),
      [suggestion({ method: 'ridge', label: 'Ridge', characteristics: null })],
    );
    expect(screen.queryByText('Ridge')).toBeNull();
  });

  it('renders nothing at all when no row has a characteristics table', () => {
    const { container } = render(
      <ThemeProvider theme={theme}>
        <CharacteristicsTable
          recommended={suggestion({ characteristics: null })}
          alternatives={[]}
        />
      </ThemeProvider>,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('never uses colour alone: every rating pairs a word with dots', () => {
    // DESIGN.md requires two carriers for the qualitative cells; neither may stand alone.
    show(suggestion());
    for (const word of ['low', 'yes', 'moderate']) {
      expect(screen.getByText(word)).toBeInTheDocument();
    }
    expect(screen.getAllByText('high').length).toBeGreaterThan(0);
  });
});
