import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';

import { chrome, spacing } from '../theme/tokens';

/**
 * One reading taken from the file, with how much it should be trusted.
 *
 * **Low confidence is flagged per field, with an icon *and* a label** — never colour
 * alone, which is unreadable to anyone who cannot distinguish the two, and never a banner
 * over the whole form, which tells someone to re-check everything and so gets re-checked
 * by nobody.
 *
 * **The flag survives re-renders until the user acts on it.** A warning that clears itself
 * has been silently accepted on their behalf, which is the outcome FR-8.2 exists to
 * prevent.
 */
export function DetectedField({
  label,
  detail,
  detected = true,
  uncertain,
  confirmed,
  onConfirm,
  children,
}: {
  label: string;
  detail: string;
  /** Whether this value was read from the file rather than answered by the user. */
  detected?: boolean;
  uncertain: boolean;
  confirmed: boolean;
  onConfirm: () => void;
  children?: React.ReactNode;
}) {
  const flagged = uncertain && !confirmed;

  return (
    <Box sx={{ mb: `${spacing.fieldGap}px` }}>
      <Typography sx={{ fontWeight: 700 }}>{label}</Typography>
      {children}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
        {flagged ? (
          // The icon repeats what the caption says rather than replacing it, so the state
          // survives a reader who cannot see the difference between amber and grey.
          <WarningAmberIcon fontSize="small" aria-hidden sx={{ color: chrome.unsure.hex }} />
        ) : (
          detected && (
            <AutoAwesomeIcon fontSize="small" aria-hidden sx={{ color: chrome.detected.hex }} />
          )
        )}
        <Typography
          variant="body2"
          component="span"
          sx={{
            color: flagged
              ? chrome.unsure.hex
              : detected
                ? chrome.detected.hex
                : 'text.secondary',
          }}
        >
          {flagged ? "We're not sure about this one — please check it." : detail}
        </Typography>
        {flagged && (
          <Button size="small" onClick={onConfirm} sx={{ ml: 1 }}>
            Looks right
          </Button>
        )}
      </Box>
    </Box>
  );
}
