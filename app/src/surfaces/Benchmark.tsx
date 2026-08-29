import Typography from '@mui/material/Typography';

/**
 * The Benchmark surface — transparency: the dataset × method evidence behind the
 * recommender, its provenance, and error reporting. Epic 6 fills it in.
 */
export function Benchmark() {
  return (
    <>
      <Typography variant="h4" component="h1" gutterBottom>
        Benchmark
      </Typography>
      <Typography color="text.secondary">
        The evidence behind the recommender. Built in Epic 6.
      </Typography>
    </>
  );
}
