import Box from '@mui/material/Box';
import { Route, Routes } from 'react-router-dom';

import { Footer } from './chrome/Footer';
import { TopBar } from './chrome/TopBar';
import { Benchmark } from './surfaces/Benchmark';
import { Dashboard } from './surfaces/Dashboard';
import { spacing } from './theme/tokens';

export function App() {
  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100vh' }}>
      <TopBar />
      <Box
        component="main"
        id="main"
        // Focusable so the skip link actually lands somewhere, but not in the tab order.
        tabIndex={-1}
        sx={{
          maxWidth: spacing.contentMax,
          mx: 'auto',
          px: { xs: `${spacing.pageMarginCompact}px`, md: `${spacing.pageMargin}px` },
          py: `${spacing.sectionGap}px`,
          outline: 'none',
        }}
      >
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/benchmark" element={<Benchmark />} />
        </Routes>
      </Box>
      <Footer />
    </Box>
  );
}
