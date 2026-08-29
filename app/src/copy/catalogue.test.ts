/**
 * The constraints on the copy, enforced where a machine can enforce them.
 *
 * The rest is a reading task and stays one — these tests catch the failures that are
 * mechanical, so a human review can spend its attention on whether the writing is any good.
 */

import { describe, expect, it } from 'vitest';

import { ALL_STRINGS, FORM_QUESTIONS, PANEL, SUSPICION_ANSWERS } from './catalogue';

const entries = Object.entries(ALL_STRINGS);
const explanations = FORM_QUESTIONS.map((q) => [q.id, q.explanation] as const);

/**
 * Naming a source is the failure FR-2.3 forbids. The theory underneath is a statistical
 * learning course; the interface must never say so, imply so, or link out to it.
 */
const CITATIONS = [
  /\bISLR\b/i,
  /\btextbook\b/i,
  /\bthe literature\b/i,
  /\bet al\b/i,
  /\bpaper\b/i,
  /\b(19|20)\d{2}\b/,
  /\b(hastie|tibshirani|witten|friedman|breiman)\b/i,
];

/**
 * Terms of art that cannot be unpacked inside two or three sentences, so they are simply
 * not used. This is not a style preference: a reader who already knows these words is not
 * the reader this copy is for.
 */
const JARGON = [
  /\boverfit/i,
  /\bvariance\b/i,
  /\bbias\b/i,
  /\bregularis|regulariz/i,
  /\bhyperparameter/i,
  /\bcross-?validat/i,
  /\bcollinear/i,
  /\bp-value/i,
  /\bnon-?linear/i,
  /\bcategorical\b/i,
  /\bnoise\b/i,
];

/** Verdicts the rule layer does not license. */
const VERDICTS = [/\bbest method\b/i, /\byou should use\b/i, /\boptimal\b/i, /\bguarantee/i];

describe('every string', () => {
  it.each(entries)('%s names no source', (_id, text) => {
    for (const pattern of CITATIONS) expect(text).not.toMatch(pattern);
  });

  it.each(entries)('%s uses no unexplained term of art', (_id, text) => {
    for (const pattern of JARGON) expect(text).not.toMatch(pattern);
  });

  it.each(entries)('%s claims no verdict the engine cannot support', (_id, text) => {
    for (const pattern of VERDICTS) expect(text).not.toMatch(pattern);
  });

  it.each(entries)('%s is not a placeholder', (_id, text) => {
    expect(text.trim().length).toBeGreaterThan(0);
    expect(text).not.toMatch(/\bTODO\b|\bTBD\b|lorem/i);
  });
});

describe('the form explanations', () => {
  it.each(explanations)('%s runs two to four sentences', (_id, text) => {
    // Long enough to define what it uses, short enough to read beneath a control. The
    // spine's specimen is four; below two, a question is being labelled rather than
    // explained.
    const sentences = text.split(/[.?!]\s+|[.?!]$/).filter(Boolean);
    expect(sentences.length).toBeGreaterThanOrEqual(2);
    expect(sentences.length).toBeLessThanOrEqual(4);
  });

  it.each(explanations)('%s explains rather than restating the label', (_id, text) => {
    expect(text.length).toBeGreaterThan(120);
  });

  it('covers every question in the no-dataset form', () => {
    // Six shape-specific fields plus the three always asked (FR-1.4).
    expect(FORM_QUESTIONS).toHaveLength(9);
  });

  it('gives every question a unique id', () => {
    const ids = FORM_QUESTIONS.map((q) => q.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('asks every label as a question', () => {
    // A label that is a noun phrase makes the user guess what is being asked of them.
    for (const question of FORM_QUESTIONS) expect(question.label).toMatch(/\?$/);
  });
});

describe('the three-option answers', () => {
  it('offers the middle answer as an answer, not an absence', () => {
    // The engine treats "I don't know" as a real answer at half strength, so the label
    // must not read as a refusal to answer. A control that looks like an opt-out gets
    // used as one.
    expect(SUSPICION_ANSWERS.map((a) => a.value)).toEqual(['no', 'unsure', 'yes']);
    expect(SUSPICION_ANSWERS[1].label).toBe("I don't know");
  });
});

describe('the recommendation panel', () => {
  it('describes the bias-variance axis without naming either end as better', () => {
    // Which end is better depends on the problem, which is what the rest of the panel is
    // for. Asserting it here would be a claim the rule layer never makes.
    const text = PANEL['panel.bias-variance.explanation'];
    expect(text).toMatch(/neither end/i);
  });

  it('keeps interpretability separate from accuracy', () => {
    // They are independent properties, and conflating them is the most common way this
    // explanation goes wrong.
    expect(PANEL['panel.interpretability.explanation']).toMatch(/nothing about which is more/i);
  });
});
