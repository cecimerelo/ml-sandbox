import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import type React from 'react';

/** The loading/error states every chart panel shares while `useChartData` is in
 * flight — `null` once there's real data to render instead. */
export function ChartFetchStatus({
  failed,
  loaded,
}: {
  failed: boolean;
  loaded: boolean;
}): React.ReactNode {
  if (failed) {
    return (
      <Typography color="text.secondary">
        We couldn't compute these charts. Try again — training itself already finished, so this
        is only the chart step.
      </Typography>
    );
  }
  if (!loaded) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress size={24} aria-label="Computing charts" />
      </Box>
    );
  }
  return null;
}
