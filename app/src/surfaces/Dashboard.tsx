import Typography from '@mui/material/Typography';

/**
 * The Dashboard — the whole product loop: characterize, recommend, explain, explore,
 * compare. Its blocks arrive with 2.3 onward; this is the surface they hang from.
 */
export function Dashboard() {
  return (
    <>
      <Typography variant="h4" component="h1" gutterBottom>
        Describe your problem
      </Typography>
      <Typography color="text.secondary">
        The form arrives with 2.3. This is the surface it hangs from.
      </Typography>
    </>
  );
}
