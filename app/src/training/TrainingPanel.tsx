import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import PauseCircleOutlineIcon from '@mui/icons-material/PauseCircleOutline';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import ScheduleIcon from '@mui/icons-material/Schedule';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import Collapse from '@mui/material/Collapse';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import { useEffect, useRef, useState } from 'react';

import type { Task } from '../api/types';
import { TRAINING, fill } from '../copy/catalogue';
import { spacing } from '../theme/tokens';
import { CHART_PANELS } from './charts/registry';
import type { MethodResult, TrainingStatus } from './types';

const POLL_INTERVAL_MS = 1000;

async function fetchJob(jobId: string): Promise<TrainingStatus | null> {
  const response = await fetch(`/api/train/${jobId}`);
  if (!response.ok) return null;
  return response.json();
}

/**
 * Which method actually scored highest so far — evidence measured on this dataset,
 * not the recommendation's own prediction. The two can disagree: `for_problem` ranks by
 * what tends to work on datasets *shaped* like this one, and a live fit only ever
 * answers for the one dataset in front of it. Updates as results land rather than only
 * once the job is done — a genuine best-so-far, not a fake one.
 */
function bestMethod(results: TrainingStatus['results']): string | null {
  let best: string | null = null;
  let bestScore = -Infinity;
  for (const [method, result] of Object.entries(results)) {
    if (result.status === 'ok' && result.mean_score !== null && result.mean_score > bestScore) {
      best = method;
      bestScore = result.mean_score;
    }
  }
  return best;
}

/**
 * Block 4 — trains the recommended methods on the user's own data (FR-4.1, FR-8.4).
 *
 * **Not automatic.** A first reading of FR-4.1 had this start the moment a recommendation
 * landed, but training is a different commitment from asking for advice — up to five real
 * fits, tens of seconds to minutes — so it waits for its own explicit click.
 *
 * **No fake progress bar.** NFR-1 asks for an honest ceiling, not a smooth animation: the
 * estimate here is `(methods not yet finished) × this job's timeout tier`, revised down
 * only when a method actually finishes, never interpolated between polls.
 */
export function TrainingPanel({
  file,
  target,
  task,
  methods,
  resetSignal,
}: {
  file: File | null;
  target: string | null;
  task: Task | null;
  /** In fit-score order, already narrowed to what the recommendation actually offered —
   * this panel does not re-rank or re-filter them. */
  methods: string[];
  /** Bumped by the caller on every new successful recommendation — stops whatever this
   * panel was doing for the *previous* one, the same contract as `EdaBlock`'s
   * `collapseSignal`. */
  resetSignal?: number;
}) {
  const [job, setJob] = useState<TrainingStatus | null>(null);
  const [failed, setFailed] = useState(false);
  const [openCharts, setOpenCharts] = useState<string | null>(null);
  const jobRef = useRef<TrainingStatus | null>(null);
  jobRef.current = job;

  useEffect(() => {
    if (resetSignal === undefined) return;
    const current = jobRef.current;
    if (current && !current.done) {
      void fetch(`/api/train/${current.id}/stop`, { method: 'POST' });
    }
    setJob(null);
    setFailed(false);
    setOpenCharts(null);
    // Deliberately keyed on `resetSignal` alone — `jobRef` is read for its current value,
    // not to be reactive to it, the same reason `EdaBlock`'s equivalent effect only
    // depends on its own signal prop.
  }, [resetSignal]);

  useEffect(() => {
    if (!job || job.done) return;
    const timer = setInterval(async () => {
      const next = await fetchJob(job.id);
      if (!next) {
        setFailed(true);
        return;
      }
      setJob(next);
    }, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [job]);

  async function start() {
    if (!file || !target || !task) return;
    setFailed(false);
    const body = new FormData();
    body.append('file', file);
    body.append('target', target);
    body.append('task', task);
    for (const method of methods) body.append('methods', method);
    const response = await fetch('/api/train', { method: 'POST', body });
    if (!response.ok) {
      setFailed(true);
      return;
    }
    const { job_id } = await response.json();
    const initial = await fetchJob(job_id);
    setJob(initial);
  }

  async function stop() {
    if (!job) return;
    await fetch(`/api/train/${job.id}/stop`, { method: 'POST' });
  }

  const disabledReason = !file
    ? TRAINING['training.button.no-dataset']
    : methods.length === 0
      ? TRAINING['training.button.none-usable']
      : null;

  const active = job !== null && !job.done;
  const remaining = job ? methods.length - Object.keys(job.results).length : 0;
  const leader = job ? bestMethod(job.results) : null;

  return (
    <Paper variant="outlined" sx={{ p: 3, mt: `${spacing.sectionGap}px` }}>
      <Typography variant="h6" component="h2" gutterBottom>
        {TRAINING['training.progress.heading']}
      </Typography>

      {!job && (
        <Box>
          <Button variant="contained" disabled={!!disabledReason} onClick={() => void start()}>
            {TRAINING['training.button.label']}
          </Button>
          {disabledReason && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {disabledReason}
            </Typography>
          )}
        </Box>
      )}

      {failed && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {TRAINING['training.error']}
        </Alert>
      )}

      {job && (
        <Box sx={{ mt: 1 }}>
          <List disablePadding>
            {methods.map((method) => {
              const ChartPanel = CHART_PANELS[method];
              const chartsOpen = openCharts === method;
              return (
                <Box key={method}>
                  <MethodRow
                    method={method}
                    result={job.results[method]}
                    current={job.current === method}
                    isBest={method === leader}
                    chartsOpen={chartsOpen}
                    onToggleCharts={
                      ChartPanel
                        ? () => setOpenCharts((current) => (current === method ? null : method))
                        : undefined
                    }
                  />
                  {ChartPanel && (
                    <Collapse in={chartsOpen} unmountOnExit>
                      {file && target && job.results[method]?.status === 'ok' && (
                        <Box sx={{ pb: 2, pl: 5 }}>
                          <ChartPanel jobId={job.id} file={file} target={target} />
                        </Box>
                      )}
                    </Collapse>
                  )}
                </Box>
              );
            })}
          </List>

          {Object.values(job.results).some((result) => result.status === 'ok') && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {TRAINING['training.score.explanation']}
            </Typography>
          )}

          {active && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                {fill(TRAINING['training.progress.estimate'], {
                  seconds: remaining * job.budget_seconds,
                })}
              </Typography>
              <Button size="small" color="secondary" onClick={() => void stop()}>
                {TRAINING['training.stop.button']}
              </Button>
            </Box>
          )}

          {job.done && job.aborted && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {job.abort_detail ?? TRAINING['training.error']}
            </Alert>
          )}

          {job.done && !job.aborted && job.halted_early && (
            <Alert severity="info" sx={{ mt: 2 }}>
              {fill(TRAINING['training.halted-early'], {
                done: Object.keys(job.results).length,
                total: methods.length,
              })}
            </Alert>
          )}
        </Box>
      )}
    </Paper>
  );
}

function MethodRow({
  method,
  result,
  current,
  isBest,
  chartsOpen,
  onToggleCharts,
}: {
  method: string;
  result: MethodResult | undefined;
  /** Whether `job.current` names this method — the only signal that it is actively
   * fitting: a `MethodResult` only exists once a method has *finished*, one way or
   * another, so "running" can never come from `result.status` itself. */
  current: boolean;
  /** Whether this method's measured score is the highest among finished methods —
   * evidence from this dataset, independent of which method the recommendation named. */
  isBest: boolean;
  chartsOpen: boolean;
  /** Present only when `method` has a chart panel implemented (#83) — a method missing
   * one gets no button at all, not a disabled one, since there is nothing to explain. */
  onToggleCharts: (() => void) | undefined;
}) {
  const status = current ? 'running' : (result?.status ?? 'pending');
  return (
    <ListItem disableGutters>
      <ListItemIcon sx={{ minWidth: 32 }}>
        <StatusIcon status={status} />
      </ListItemIcon>
      <ListItemText
        primary={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {method}
            {isBest && (
              <Chip size="small" color="success" label={TRAINING['training.best-result']} />
            )}
          </Box>
        }
        secondary={secondaryText(method, status, result)}
      />
      {status === 'ok' && onToggleCharts && (
        <Button size="small" onClick={onToggleCharts}>
          {chartsOpen ? 'Hide charts' : 'View charts'}
        </Button>
      )}
    </ListItem>
  );
}

function StatusIcon({ status }: { status: MethodResult['status'] | 'pending' }) {
  switch (status) {
    case 'ok':
      return <CheckCircleOutlineIcon color="success" fontSize="small" />;
    case 'timeout':
      return <ScheduleIcon color="warning" fontSize="small" />;
    case 'error':
      return <ErrorOutlineIcon color="error" fontSize="small" />;
    case 'stopped':
      return <PauseCircleOutlineIcon color="disabled" fontSize="small" />;
    case 'running':
      return <CircularProgress size={16} />;
    default:
      return <RadioButtonUncheckedIcon color="disabled" fontSize="small" />;
  }
}

function secondaryText(
  method: string,
  status: MethodResult['status'] | 'pending',
  result: MethodResult | undefined,
): string | undefined {
  if (status === 'running') return fill(TRAINING['training.progress.current'], { method });
  if (status === 'ok') return `Score: ${result?.mean_score?.toFixed(2)}`;
  if (status === 'timeout') {
    return fill(TRAINING['training.timeout'], {
      method,
      seconds: result?.fit_seconds?.toFixed(0) ?? '?',
    });
  }
  if (status === 'stopped') return TRAINING['training.stop.confirmation'];
  if (status === 'error') return result?.detail ?? undefined;
  return undefined;
}
