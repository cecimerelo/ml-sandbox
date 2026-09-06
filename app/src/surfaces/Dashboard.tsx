import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { useEffect, useRef, useState } from 'react';

import type { RecommendationRequest } from '../api/types';
import { EdaBlock } from '../eda/EdaBlock';
import { FormSummaryBar } from '../form/FormSummaryBar';
import { ProblemForm } from '../form/ProblemForm';
import { RecommendationPanel } from '../panel/RecommendationPanel';
import type { Recommendation } from '../panel/types';
import { DatasetPanel } from '../detect/DatasetPanel';
import type { Detection } from '../detect/types';
import { Dropzone } from '../upload/Dropzone';
import type { DatasetSummary } from '../upload/Dropzone';
import { spacing } from '../theme/tokens';

/**
 * The Dashboard — the whole product loop: characterize, recommend, explain, explore,
 * compare.
 *
 * Block 1 is here. Block 2, the recommendation panel, arrives with 2.4 once 2.2 gives it
 * something to render; until then the submitted answers are shown so the form can be
 * exercised end to end.
 */
export function Dashboard() {
  const [result, setResult] = useState<Recommendation | null>(null);
  const [failed, setFailed] = useState<string | null>(null);
  const [stale, setStale] = useState(false);
  const [dataset, setDataset] = useState<{ file: File; summary: DatasetSummary } | null>(null);
  const [detection, setDetection] = useState<Detection | null>(null);
  // Whether the full form is on screen rather than its collapsed one-line summary.
  // Irrelevant until a recommendation exists — there is nothing yet to collapse to, so the
  // form always renders expanded before the first successful run regardless of this.
  const [editing, setEditing] = useState(true);
  const formRef = useRef<HTMLDivElement>(null);
  const resultRef = useRef<HTMLDivElement>(null);

  async function ask(request: RecommendationRequest) {
    setFailed(null);
    setStale(false);
    // Cleared before the request. Leaving the previous recommendation on screen while a
    // new one is computed shows an answer to a question the user has already changed.
    setResult(null);
    try {
      const response = await fetch('/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });
      if (!response.ok) {
        setFailed('We could not work out a recommendation for that. Try again.');
        return;
      }
      setResult(await response.json());
      // Collapsing here, not only via `Done`, is what "or automatically on the next Get
      // Recommendation" means: a re-run from the expanded form puts the summary bar back
      // without a second click.
      setEditing(false);
    } catch {
      setFailed(
        "We couldn't reach the server, so nothing has been worked out yet. If you're " +
          'running this locally, check the API is up.',
      );
    }
  }

  // Moves focus to the first field on `Edit`. Not on the initial mount, where nothing has
  // been collapsed yet and stealing focus from wherever the page landed would be its own
  // surprise.
  const editingRef = useRef(editing);
  useEffect(() => {
    if (editing && !editingRef.current) {
      formRef.current?.querySelector<HTMLElement>('input[type="radio"]')?.focus();
    }
    editingRef.current = editing;
  }, [editing]);

  // On a successful run, the page scrolls to the top and focus moves to the recommendation
  // heading — the spine's own focus contract, not merely a nicety: someone who cannot see
  // the page (a screen reader, a zoomed viewport) is otherwise left exactly where they
  // clicked, with no way to tell the click did anything.
  //
  // To the top of the page, not the heading scrolled into view: the form collapsing to
  // the summary bar shortens everything above the panel, and scrolling only the heading
  // into view can leave the reader mid-page with the summary bar and top bar off-screen
  // above them, no less disorienting than not scrolling at all.
  useEffect(() => {
    if (!result) return;
    window.scrollTo({ top: 0 });
    const heading = resultRef.current?.querySelector<HTMLElement>('h2');
    if (!heading) return;
    heading.tabIndex = -1;
    // `preventScroll`: the window scroll above is already the scroll this needs: focusing
    // without it would let the browser scroll the heading to its own idea of "into view",
    // fighting the scroll just set.
    heading.focus({ preventScroll: true });
  }, [result]);

  return (
    <>
      {/* Centred in a reading column rather than filling the page. Text stays left-aligned
          inside it: a centred paragraph gives every line a different starting point, and the
          eye has to hunt for each one. */}
      <Box sx={{ maxWidth: spacing.readingMax, mx: 'auto' }}>
        {/* The heading and its one-line intro are centred; the questions below are not.
            A heading is a landmark and reads fine centred, but centring the explanations
            would give every line a different starting point, and the eye has to hunt for
            each one. */}
        <Typography variant="h4" component="h1" align="center" gutterBottom>
          Describe your problem
        </Typography>
        <Typography color="text.secondary" align="center" sx={{ mb: 5 }}>
          Answer what you can about your data and we will suggest a method, with the reasoning
          behind it. You do not need to upload anything.
        </Typography>

        {/* Above the form, and above the summary bar it collapses to — never hidden by
            either, so removing or replacing the dataset is always reachable, and so is
            what's below it. */}
        <Dropzone
          onAccepted={(file, summary) => {
            setDataset({ file, summary });
            // A new file invalidates the old reading. Leaving it would fill the
            // questions with properties of a dataset nobody uploaded.
            setDetection(null);
          }}
          onCleared={() => {
            setDataset(null);
            setDetection(null);
            // The recommendation was worked out from this file's detections. Marking
            // it stale rather than clearing it would leave a reader looking at a
            // dimmed answer to a question the form can no longer even ask — removing
            // the file took the premise with it, not just made the answer old.
            setResult(null);
            setStale(false);
          }}
        />

        {/* Block 3. Right after the upload's own summary line ("400 rows, 5 usable
            columns"), not after the whole form or the recommendation below it — a
            reader who just uploaded a file is looking at this part of the screen, and
            anywhere further down was going undiscovered. Present only with a dataset
            and a chosen target (FR-3.1). Also outside the collapsible section below,
            same reason as the dropzone: collapsing the answered questions to their
            one-line summary is not a reason to also hide the data explorer that answers
            a different question entirely. */}
        {dataset && detection && (
          <EdaBlock file={dataset.file} target={detection.target} />
        )}

        {/* Once a recommendation exists, the form itself is the exception rather than the
            rule: most of a long results page is spent reading below it, and the summary
            bar is the one-click way back up. Before that first run there is nothing to
            collapse to, so the summary bar never shows regardless of `editing`.
            Hidden with `display`, not unmounted: `ProblemForm` owns its own answer state,
            and swapping it out of the tree for the summary bar would lose every answer
            the moment `Edit` tried to bring it back. */}
        {result && !editing && <FormSummaryBar onEdit={() => setEditing(true)} />}
        <Box ref={formRef} sx={{ display: result && !editing ? 'none' : 'block' }}>
          {/* Choosing the outcome comes before anything else the file can say, because
              every other reading depends on it. The questions below still have to be
              answered by hand — carrying the detections into them is the shape switch,
              which is its own task. */}
          {dataset && (
            <DatasetPanel
              file={dataset.file}
              columns={dataset.summary.columns}
              unusable={dataset.summary.skipped}
              onDetected={setDetection}
            />
          )}

          <ProblemForm
            onSubmit={ask}
            detection={detection}
            // Only meaningful once there is a recommendation on screen for the answers
            // to outrun. The form itself never recomputes on change (FR-1.7) — this
            // only flags that what's showing was worked out from answers that no
            // longer match.
            {...(result ? { onChange: () => setStale(true) } : {})}
          />

          {/* Only once there is something to collapse back to — re-expanding via `Edit`
              is not itself a reason to force a re-run through `Get Recommendation`. */}
          {result && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <Button onClick={() => setEditing(false)}>Done</Button>
            </Box>
          )}

          {failed && (
            <Alert severity="error" sx={{ mt: 4 }}>
              {failed}
            </Alert>
          )}
        </Box>
      </Box>
      <div ref={resultRef}>
        <DashboardResult result={result} failed={failed} stale={stale} />
      </div>
    </>
  );
}

function DashboardResult({
  result,
  failed,
  stale,
}: {
  result: Recommendation | null;
  failed: string | null;
  stale: boolean;
}) {
  if (!result || failed) return null;
  // Wider than the reading column above it, and sized to its own content rather than a
  // fixed measure: "Method characteristics" needs more than 640px to lay out five columns
  // without a scrollbar, and the panel should be exactly as wide as that table needs to
  // be, not narrower with a scrollbar or wider with empty margin.
  return (
    <Box sx={{ width: 'fit-content', maxWidth: spacing.contentMax, mx: 'auto' }}>
      <RecommendationPanel result={result} stale={stale} />
    </Box>
  );
}
