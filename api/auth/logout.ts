import { destroySession } from '../_lib/auth';
import { privateWriteRoute } from '../_lib/route';

export default privateWriteRoute(async function handler({ req, res }) {
  await destroySession(req, res);
  return { ok: true };
});
