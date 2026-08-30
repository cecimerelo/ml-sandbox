/**
 * The glossary — terms of art the copy is allowed to use, and what they mean.
 *
 * A departure from the experience spine, which rules out an expandable glossary as
 * progressive disclosure (D-040). Two objections drove that rule and both are answered by
 * how this is built rather than by not building it:
 *
 * **"You have to know that you don't know."** A definition behind an unmarked word only
 * reaches a reader who already suspects the word. So glossed terms are *visibly marked* —
 * the reader sees that a definition exists without having to guess. That is the whole
 * difference between a glossary and a trap.
 *
 * **Hover does not exist on touch or keyboard.** So `Term` opens on focus and on tap too,
 * and carries `aria-describedby` rather than relying on a visual popup.
 *
 * The catalogue's jargon rule becomes a completeness check instead of a ban: a term of art
 * may appear in the copy **if and only if** it is defined here. That is stronger than a
 * blocklist, which only catches the words someone thought to list.
 *
 * Definitions obey the same constraints as the rest of the copy — citation-free, and
 * defining a term without leaning on another undefined one.
 */

export interface Definition {
  term: string;
  /** One or two sentences. A definition that needs a paragraph belongs in the copy. */
  definition: string;
}

export const GLOSSARY: Record<string, Definition> = {
  noise: {
    term: 'noise',
    definition:
      'Variation in your data that comes from chance rather than from a real pattern — ' +
      'the part that would come out differently if you collected the data again.',
  },
  overfitting: {
    term: 'overfitting',
    definition:
      'When a method describes the data it was trained on almost perfectly, including the ' +
      'accidents in it, and then does badly on anything new.',
  },
  variance: {
    term: 'variance',
    definition:
      'How much a method changes its mind when you give it a different sample of the same ' +
      'kind of data. High variance means small changes in the data produce large changes ' +
      'in the answer.',
  },
  bias: {
    term: 'bias',
    definition:
      'How much a method is off because of the shape it assumes in advance. A method that ' +
      'only draws straight lines has high bias on a relationship that curves — not because ' +
      'it is careless, but because a curve is not something it can draw.',
  },
  'bias-variance trade-off': {
    term: 'bias-variance trade-off',
    definition:
      'Assuming less about the shape of the pattern lets a method follow the data more ' +
      'closely, but also makes it swing more between samples. Most of choosing a method is ' +
      'choosing where on that scale you want to sit.',
  },
  regularisation: {
    term: 'regularisation',
    definition:
      'Deliberately holding a method back — shrinking how much weight it gives each ' +
      'column, or dropping some entirely — so it cannot chase every wobble in the data.',
  },
  'cross-validation': {
    term: 'cross-validation',
    definition:
      'Splitting the data into parts, training on all but one, and scoring on the part ' +
      'held back. Repeating that for each part gives a score on data the method has not ' +
      'seen, which is the only kind worth reporting.',
  },
  'standard deviation': {
    term: 'standard deviation',
    definition:
      'A measure of how spread out a set of numbers is. Two scores within one standard ' +
      'deviation of each other are close enough that the difference could easily be chance.',
  },
  'balanced accuracy': {
    term: 'balanced accuracy',
    definition:
      'Accuracy that counts each category equally, however rare it is. Plain accuracy can ' +
      'look excellent while a method ignores a small category completely; this does not.',
  },
  'categorical column': {
    term: 'categorical column',
    definition:
      'A column holding labels rather than numbers you can do arithmetic with — a city, a ' +
      'blood type, a product category.',
  },
  interaction: {
    term: 'interaction',
    definition:
      'When two columns only matter in combination — a treatment that helps at one age and ' +
      'harms at another. Neither column tells the story on its own.',
  },
  ensemble: {
    term: 'ensemble',
    definition:
      'A method that trains many simple models and combines their answers. The combination ' +
      'is usually more accurate than any one of them, and much harder to explain.',
  },
  imputation: {
    term: 'imputation',
    definition:
      'Filling in missing cells with a guess — often the column average — so a method that ' +
      'cannot read a blank can still be trained. The guess becomes part of what it learns.',
  },
};

export const GLOSSARY_TERMS = Object.keys(GLOSSARY);
