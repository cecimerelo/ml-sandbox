import { Fragment } from 'react';

import { Term } from './Term';

/**
 * Turn a catalogue string into nodes, expanding `{{term}}` into a glossed term.
 *
 * The catalogue stays plain text because a supervisor has to read it as writing, and a
 * file of JSX is not writing. `{{noise}}` is legible in a review and unambiguous to a
 * parser, which is the whole requirement.
 */
export function renderCopy(text: string) {
  return text.split(/(\{\{[^}]+\}\})/).map((part, index) => {
    const match = /^\{\{([^}]+)\}\}$/.exec(part);
    return (
      <Fragment key={index}>
        {match?.[1] ? <Term name={match[1]} /> : part}
      </Fragment>
    );
  });
}

/** The plain reading of a string, with the markers removed. For tests and for prose length. */
export function plainText(text: string): string {
  return text.replace(/\{\{([^}]+)\}\}/g, '$1');
}

/** Which glossary terms a string marks. */
export function termsIn(text: string): string[] {
  return [...text.matchAll(/\{\{([^}]+)\}\}/g)].map((m) => m[1] as string);
}
