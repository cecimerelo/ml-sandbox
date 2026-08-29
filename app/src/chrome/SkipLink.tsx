import Link from '@mui/material/Link';

/**
 * The first tab stop on every surface, visually hidden until focused.
 *
 * The top bar holds two tab stops before any content. Without this, a keyboard user
 * re-traverses them on every page — which is not a large cost per page and is a large cost
 * per session.
 *
 * Not `display: none` or `visibility: hidden`: both remove it from the focus order, which
 * is the one thing it exists to be in. The clip-rect idiom keeps it focusable.
 */
export function SkipLink() {
  return (
    <Link
      href="#main"
      sx={{
        position: 'absolute',
        left: -10000,
        width: 1,
        height: 1,
        overflow: 'hidden',
        '&:focus': {
          position: 'static',
          width: 'auto',
          height: 'auto',
          p: 1,
          display: 'inline-block',
        },
      }}
    >
      Skip to main content
    </Link>
  );
}
