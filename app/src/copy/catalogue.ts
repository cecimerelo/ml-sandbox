/**
 * The explanation catalogue — every pre-authored string the product shows, in one place.
 *
 * One artifact, keyed by string ID, rather than copy scattered through components. A
 * supervisor has to be able to read the pedagogy as a body of writing and sign it off as
 * content, separately from the code, and that is impossible if it lives in forty JSX files.
 *
 * Four hard constraints, enforced by `catalogue.test.ts` where a machine can check them:
 *
 * 1. **Citation-free.** No textbook, paper, author, year, or "the literature". The theory
 *    underneath is a statistical learning course; the interface never says so.
 * 2. **No prior knowledge assumed.** Any term of art is unpacked in the same breath, or
 *    not used.
 * 3. **No claim stronger than the rule that produced it.** Where the engine knows "few
 *    rows and interpretability critical → prefer a simpler method", the copy says why it
 *    was preferred, never that it *is* better.
 * 4. **No progressive disclosure.** No "learn more", no glossary, no tour. Education is
 *    always visible or it is not there.
 *
 * Grounding lives in `docs/copy-traceability.md`, a thesis appendix — never in the UI.
 */

export interface Question {
  /** Stable ID. What the record stores and the traceability table keys on. */
  id: string;
  label: string;
  /** Always visible beneath the control (FR-1.6). Two to three sentences. */
  explanation: string;
}

/**
 * Shape B — the no-dataset form. Order matches the spine's field order.
 *
 * Shape A replaces the first six with detections and needs its own variants, which arrive
 * with 3.2: the question there is "is this right?", not "what is it?", and copy written
 * for one does not answer the other.
 */
export const FORM_QUESTIONS: Question[] = [
  {
    id: 'form.prediction-type',
    label: 'What are you trying to predict?',
    explanation:
      'A number, like a price or a temperature, is a different problem from a category, ' +
      'like whether an email is spam. Methods are built for one or the other, so this ' +
      'answer decides which ones are even available to you.',
  },
  {
    id: 'form.rows',
    label: 'Roughly how many rows does your data have?',
    explanation:
      'A row is one example — one house, one patient, one transaction. Methods that can ' +
      'describe complicated patterns need a lot of examples to tell a real pattern from ' +
      'coincidence, so with few rows a simpler method often does better.',
  },
  {
    id: 'form.features',
    label: 'How many columns are you predicting from?',
    explanation:
      "These are the things you already know about each row — a house's size, age and " +
      'location. Not the thing you are trying to predict. The more columns there are ' +
      'relative to rows, the easier it is for a method to find patterns that are not there.',
  },
  {
    id: 'form.feature-types',
    label: 'What kind of columns are they?',
    explanation:
      'Numbers you can do arithmetic with, like age or price, behave differently from ' +
      'labels like city or blood type. Some methods work with labels directly; others ' +
      'need them converted into numbers first, which can go badly when there are many ' +
      'distinct labels. A column of labels is a {{categorical column}}.',
  },
  {
    id: 'form.missing',
    label: 'How much of your data is missing?',
    explanation:
      'Blank cells — a survey question nobody answered, a sensor that dropped out. Most ' +
      'methods cannot read a blank, so the gaps have to be filled in with a guess before ' +
      'training. That filling-in is called {{imputation}}, and the more gaps there are, ' +
      'the more it shapes the result.',
  },
  {
    id: 'form.class-balance',
    label: 'Are your categories about the same size?',
    explanation:
      'If ninety-nine of every hundred rows are one category, a method can score very ' +
      'well by always guessing that one and never being useful. Knowing this in advance ' +
      'changes both which method suits you and how its score should be read.',
  },
  {
    id: 'form.explainability',
    label: 'Do you need to explain individual predictions?',
    explanation:
      'Not whether the method is simple — whether you will have to tell someone why ' +
      'their particular case came out the way it did. Some methods hand you the reason ' +
      'directly; others give an answer with no reason attached. If a decision has to be ' +
      'defended, that difference matters more than accuracy does.',
  },
  {
    id: 'form.non-linearity',
    label: 'Do you think the pattern in your data is a straight line?',
    explanation:
      'Some methods can only draw straight relationships — as one number goes up, the ' +
      'other goes up or down at a steady rate. Others can bend. If you already know the ' +
      'relationship curves, levels off, or flips direction somewhere, say so and we will ' +
      "prefer a method that can follow it. If you don't know, say so — that's a real " +
      'answer and we will treat it as one.',
  },
  {
    id: 'form.interactions',
    label: 'Do any of your columns only matter in combination?',
    explanation:
      'Sometimes two things matter together in a way neither does alone — a medication ' +
      'that helps at one age and harms at another. Some methods find these combinations ' +
      'on their own; others treat every column separately and miss such an {{interaction}} ' +
      "entirely unless someone points it out. If you don't know, say so and we will hedge.",
  },
];

/** The three answers the always-asked questions share, so they read as one rhythm. */
export const SUSPICION_ANSWERS = [
  { value: 'no', label: 'No' },
  { value: 'unsure', label: "I don't know" },
  { value: 'yes', label: 'Yes' },
] as const;

/**
 * The recommendation panel's prose (FR-2.2).
 *
 * These describe an axis so a reader can place the recommendation on it. They deliberately
 * do not say which end is better: which end is better depends on the problem, and that is
 * what the rest of the panel is for.
 */
export const PANEL = {
  'panel.bias-variance.heading': 'How closely this method follows your data',
  'panel.bias-variance.explanation':
    'Methods sit on a scale. At one end they assume a simple shape and stick to it, which ' +
    'means they miss detail but stay steady when the data changes. At the other they ' +
    'follow the data closely, catching detail but also catching {{noise}}, so they can ' +
    'shift a lot when the data does. Neither end is the right one — it depends on how ' +
    'much data you have and how complicated the real pattern is.',

  'panel.interpretability.heading': 'Whether you can explain its answers',
  'panel.interpretability.explanation':
    'Some methods show you the reasoning behind a single prediction: the questions asked, ' +
    'or the weight given to each column. Others produce an answer with no reason you can ' +
    'read back. This says nothing about which is more accurate — only about what you will ' +
    'be able to tell someone who asks.',

  'panel.factors.heading': 'What led to this',
  'panel.provenance.link': 'Where does this come from?',

  'panel.suggested-method.label': 'Suggested method',
  'panel.chosen-method.subject': 'The chosen method',
  'panel.no-reasons':
    'Nothing about your problem pushed strongly in any direction, so this is the method ' +
    'that does best on data in general.',
  'panel.stale':
    'Your answers have changed since this recommendation was worked out. Press "Get ' +
    'Recommendation" again to update it.',

  'panel.flowchart.heading': 'How the engine got here',
  'panel.flowchart.no-checkpoints':
    'None of your answers pushed this choice in particular — {method} is simply the ' +
    'strongest performer on data in general, based on the benchmark.',
  'panel.flowchart.discarded-heading': 'What we discarded',
  'panel.flowchart.recommended': 'recommended',

  'panel.alternatives.heading': 'Other methods worth considering',
  'panel.tied.chip': '≈ tied',
  'panel.tied.title':
    'Too close to call apart from {method} — the model does not distinguish them.',

  'panel.characteristics.heading': 'Method characteristics',
  'panel.characteristics.column.method': 'Method',
  'panel.characteristics.column.interpretability': 'Interpretability',
  'panel.characteristics.column.non-linearity': 'Handles non-linearity',
  'panel.characteristics.column.missing-values': 'Handles missing values',
  'panel.characteristics.column.accuracy': 'Accuracy potential',
  'panel.characteristics.column.speed': 'Training speed',

  'panel.excluded.heading': 'Ruled out by what you told us',
  'panel.excluded.explanation':
    'You said you need to explain individual predictions, so these are not available — ' +
    'even where they would score better.',

  'panel.disclaimer':
    'This suggestion is based only on your answers to the form — nothing here has been ' +
    'trained or tested on your own data.',
  'panel.evidence.some':
    'Based on {total} datasets, of which {datasets} resembled yours on {field}.',
  'panel.evidence.none':
    'No dataset in the study had an answer like yours for {field}, so this suggestion is ' +
    'worked out from neighbouring cases rather than measured on data like yours.',
  'panel.provisional': 'This is built on an unfinished benchmark, so treat it as provisional.',
} as const;

/**
 * `{typography.chart-subtitle}` — the beginner-facing "what am I looking at" line every
 * plot panel carries (DESIGN.md § Chart Behavior Contract, #48). Describes **how to read
 * the chart**, never what the result means: that is the difference between "each bar is
 * a range of values" and "your data looks roughly normal", and only the first belongs
 * here — the second is a claim about the reader's own data that nothing here can make.
 *
 * `PANEL`'s truncation disclosures (the categorical fold, the correlation cap) are
 * appended to these at render time rather than folded in here — a subtitle is either
 * true of every instance of the chart or it is not one of these strings.
 */
export const CHART = {
  'chart.histogram.subtitle':
    'Each bar is a range of values; its height is how many rows fall in it.',
  'chart.categorical-bars.subtitle':
    'Each bar is one category; its length is how many rows have it.',
  'chart.boxplot.subtitle':
    'The box spans the middle half of your values; dots beyond the whiskers are ' +
    'unusually far from the rest.',
  'chart.correlation.subtitle':
    'Blue means two columns rise together, red means one rises as the other falls, ' +
    'pale means barely any relationship.',
} as const;

/**
 * `{components.training-panel}` — Block 4 (#82): the button that trains the recommended
 * methods on the user's own data, and what the panel says while that runs.
 */
export const TRAINING = {
  'training.button.label': 'Train these methods on your data',
  'training.button.no-dataset': 'Upload a file above to train this method on your own data.',
  'training.button.none-usable':
    'Every method here was ruled out by what you told us, so there is nothing left to train.',
  'training.progress.heading': 'Training on your data',
  'training.progress.current': 'Training {method}…',
  'training.progress.estimate': 'Up to {seconds}s left, based on how many methods remain.',
  'training.stop.button': 'Stop training',
  'training.stop.confirmation': 'Training stopped. Results for finished methods still show below.',
  'training.timeout':
    '{method} took longer than {seconds}s and was stopped. The other methods are unaffected.',
  'training.halted-early':
    'Stopped after {done} of {total} methods — the leading ones were already too close to ' +
    'call apart, so training the rest would not have changed the answer.',
  'training.error':
    "Something went wrong training on your data, so this run didn't finish. Try again.",
} as const;

/**
 * Fill a `{placeholder}` template from the catalogue with a value the interface computed.
 *
 * Single braces, never `{{double}}` — that syntax means a glossed term (`render.tsx`), and
 * reusing it here would make `renderCopy` try to gloss a dataset count.
 */
export function fill(template: string, values: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (_, key: string) => String(values[key] ?? `{${key}}`));
}

/** Every string, flat, for the checks that apply to all of them. */
export const ALL_STRINGS: Record<string, string> = {
  ...Object.fromEntries(
    FORM_QUESTIONS.flatMap((q) => [
      [`${q.id}.label`, q.label],
      [`${q.id}.explanation`, q.explanation],
    ]),
  ),
  ...PANEL,
  ...CHART,
  ...TRAINING,
};
