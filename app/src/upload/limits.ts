/**
 * The one rule that cannot live only on the server.
 *
 * Every other refusal is decided by the backend, which keeps each limit next to the
 * sentence that explains it so the two cannot disagree. Size is the exception: the point
 * of the check is that an oversized file **never crosses the wire**, and a check that
 * happens after the upload has happened is not that check.
 *
 * So this number exists in two places. `tests/test_upload.py` asserts they are the same
 * one, because a duplicated constant that nothing compares is a divergence waiting.
 */
export const MAX_BYTES = 50 * 1024 * 1024;

export const MAX_MEGABYTES = MAX_BYTES / 1024 / 1024;

/** Phrased like the server's, so a user cannot tell which half refused their file. */
export function tooLargeMessage(bytes: number): string {
  return `This file is ${Math.round(bytes / 1024 / 1024)} MB. The limit is ${MAX_MEGABYTES} MB.`;
}
