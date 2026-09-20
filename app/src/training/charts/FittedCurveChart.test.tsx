import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it } from 'vitest';

import { FittedCurveChart } from './FittedCurveChart';
import type { ScatterPoint } from './types';

function curve(): ScatterPoint[] {
  return [
    { x: 60, y: 100 },
    { x: 80, y: 140 },
    { x: 100, y: 200 },
    { x: 120, y: 280 },
  ];
}

function actual(): ScatterPoint[] {
  return [
    { x: 65, y: 95 },
    { x: 95, y: 210 },
  ];
}

it('draws the fitted curve and the real rows', () => {
  const { container } = render(
    <FittedCurveChart feature="size_m2" curve={curve()} actual={actual()} />,
  );
  expect(container.querySelector('polyline')).toBeInTheDocument();
  expect(container.querySelectorAll('circle')).toHaveLength(actual().length);
});

it('names the feature in the image description', () => {
  render(<FittedCurveChart feature="size_m2" curve={curve()} actual={actual()} />);
  const image = screen.getByRole('img');
  expect(image.getAttribute('aria-label')).toMatch(/Fitted curve over size_m2/);
});

it('reveals a real row\'s value on hover', async () => {
  const user = userEvent.setup();
  render(<FittedCurveChart feature="size_m2" curve={curve()} actual={actual()} />);

  const point = screen.getByLabelText('size_m2 65.0, actual 95.0');
  await user.hover(point);
  expect(await screen.findByRole('tooltip')).toHaveTextContent('size_m2 65.0, actual 95.0');
});

it('renders nothing broken when there is no curve to plot', () => {
  render(<FittedCurveChart feature="" curve={[]} actual={[]} />);
  expect(screen.getByRole('img')).toBeInTheDocument();
});
