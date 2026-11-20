// Builds the Singularity + Pac-Man profile artwork from live GitHub data.
// Artwork code adapted from README Templates by Anandhu Suresh (GPL-3.0, see LICENSE and NOTICE.md).
//
//   GITHUB_TOKEN=... node generator/build.mjs <username> <outDir>
//   node generator/build.mjs --demo <outDir>        (sample data, no network)
import { mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import * as sing from './templates/singularity/art.js';
import * as pac from './templates/pacman/art.js';
import { seededRandom } from './lib/random.js';

const here = dirname(fileURLToPath(import.meta.url));
const config = JSON.parse(readFileSync(join(here, 'config.json'), 'utf8'));

async function gql(token, query, variables) {
  let last;
  for (let attempt = 0; attempt < 4; attempt++) {
    try {
      const res = await fetch('https://api.github.com/graphql', {
        method: 'POST',
        headers: { Authorization: `bearer ${token}`, 'Content-Type': 'application/json', 'User-Agent': 'profile-art' },
        body: JSON.stringify({ query, variables }),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${JSON.stringify(body).slice(0, 300)}`);
      if (body.errors?.length) throw new Error(`GraphQL: ${body.errors[0].message}`);
      return body.data;
    } catch (e) {
      last = e;
      await new Promise((r) => setTimeout(r, 3000 * (attempt + 1)));
    }
  }
  throw last;
}

async function fetchProfile(login, token) {
  const q = `query($u:String!){ user(login:$u){
      login name bio createdAt followers { totalCount }
      repositories(first:100, ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC){ nodes { stargazerCount } }
      contributionsCollection { contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } } } } }`;
  const u = (await gql(token, q, { u: login })).user;
  const cal = u.contributionsCollection.contributionCalendar;
  const days = cal.weeks.flatMap((w) => w.contributionDays).map((d) => ({ date: d.date, count: d.contributionCount }));

  // All-time total: one call per year since the account was created.
  let allTime = 0;
  const yq = `query($u:String!,$f:DateTime!,$t:DateTime!){ user(login:$u){ contributionsCollection(from:$f,to:$t){ contributionCalendar { totalContributions } } } }`;
  let cur = new Date(u.createdAt);
  const now = new Date();
  while (cur < now) {
    const end = new Date(Math.min(cur.getTime() + 364 * 86400000, now.getTime()));
    const d = await gql(token, yq, { u: login, f: cur.toISOString(), t: end.toISOString() });
    allTime += d.user.contributionsCollection.contributionCalendar.totalContributions;
    cur = end;
  }
  return {
    login: u.login,
    joinedYear: new Date(u.createdAt).getFullYear(),
    followers: u.followers.totalCount,
    totalStars: u.repositories.nodes.reduce((s, r) => s + r.stargazerCount, 0),
    contributions: { total: cal.totalContributions, days },
    allTime,
  };
}

function demoProfile() {
  const rand = seededRandom('demo');
  const days = [];
  const today = new Date();
  for (let i = 364; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    const wk = d.getDay() === 0 || d.getDay() === 6;
    days.push({ date: d.toISOString().slice(0, 10), count: rand() < (wk ? 0.2 : 0.75) ? Math.round(rand() * (i < 120 ? 18 : 8)) : 0 });
  }
  const total = days.reduce((s, d) => s + d.count, 0);
  return { login: 'ZPatelDBS', joinedYear: 2025, followers: 0, totalStars: 0, contributions: { total, days }, allTime: total + 40 };
}

const [arg, outDir = 'dist'] = process.argv.slice(2);
try {
  const live = arg === '--demo' ? demoProfile() : await fetchProfile(arg, process.env.CONTRIB_TOKEN || process.env.GITHUB_TOKEN);
  const profile = {
    ...live,
    name: config.name,
    headline: config.headline,
    stack: config.stack,
    languages: [],
    // The ghosts are the areas you work in (your code is private, so there are no public repos to use).
    repos: config.ghosts.map((g) => ({ name: g.name, description: g.description, url: '', stars: 0, language: g.language || '' })),
    featured: config.ghosts.map((g) => g.name),
  };
  mkdirSync(outDir, { recursive: true });
  const files = {};
  for (const theme of ['dark', 'light']) {
    files[`singularity-hero-${theme}.svg`] = sing.heroSvg(profile, theme, { missionName: config.missionName });
    files[`singularity-telemetry-${theme}.svg`] = sing.telemetrySvg(profile, theme, { missionName: config.missionName });
    files[`pacman-arcade-${theme}.svg`] = pac.heroSvg(profile, theme, { role: config.playerClass });
    files[`pacman-scoreboard-${theme}.svg`] = pac.scoreSvg(profile, theme);
    files[`pacman-end-${theme}.svg`] = pac.endSvg(profile, theme, { signoff: config.signoff });
  }
  for (const [name, svg] of Object.entries(files)) writeFileSync(join(outDir, name), svg);
  console.log(`wrote ${Object.keys(files).length} files: ${live.contributions.total} contributions this year, ${live.allTime} all-time`);
} catch (e) {
  console.error(e);
  console.log(`::error title=Profile artwork failed::${String(e.message || e).replace(/\n/g, ' ').slice(0, 400)}`);
  process.exit(1);
}
