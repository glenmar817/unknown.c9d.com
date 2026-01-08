const VALUES = [
  4, 6, 26, 18, 12, 4, 12, 18, 11, 11, 17, 12, 12,
  11, 9, 12, 8, 12, 9, 6, 9, 9, 6, 13, 2, 3
];

const VALUE_LL = 24; // LL
const VALUE_Ñ = 11; // Ñ

function letterValue(token) {
  if (!token) return 0;
  if (token === 'LL') return VALUE_LL;
  if (token === 'Ñ') return VALUE_Ñ;

  const code = token.charCodeAt(0);
  if (code >= 65 && code <= 90) {
    return VALUES[code - 65];
  }
  return 0;
}

function tokenizeName(raw) {
  const cleaned = raw.replace(/\s+/g, '');
  const tokens = [];

  for (let i = 0; i < cleaned.length; i++) {
    const ch = cleaned[i];

    if (ch === 'ñ' || ch === 'Ñ') {
      tokens.push('Ñ');
      continue;
    }

    const next = cleaned[i + 1];
    if ((ch === 'L' || ch === 'l') && (next === 'L' || next === 'l')) {
      tokens.push('LL');
      i++;
      continue;
    }

    tokens.push(ch.toUpperCase());
  }

  return tokens;
}

function computePairs(name) {
  if (!name.trim()) return 'Please enter a name.';

  const words = name.trim().split(/\s+/); // split by spaces
  let total = 0;
  let lines = [];

  words.forEach((word, wordIndex) => {
    const tokens = tokenizeName(word);

    for (let i = 0; i < tokens.length; i += 2) {
      const t1 = tokens[i];
      const v1 = letterValue(t1);

      if (i + 1 < tokens.length) {
        const t2 = tokens[i + 1];
        const v2 = letterValue(t2);

        lines.push(
          `${t1.padEnd(2)} +  ${t2.padEnd(3)} | ${String(v1).padEnd(2)} + ${String(v2).padEnd(2)} | = ${v1 + v2}`
        );

        total += v1 + v2;
      } else {
        lines.push(
          `${t1.padEnd(2)}        | ${String(v1).padEnd(2)}      | = ${String(v1).padEnd(2)}`
        );

        total += v1;
      }
    }

    // blank line after each word (except last)
    if (wordIndex < words.length - 1) {
      lines.push('');
    }
  });

  lines.push('');
  lines.push(`Your Spiritual Number : ${total}`);

  return lines.join('\n');
}


const nameInput = document.getElementById('name');
const output = document.getElementById('output');

document.getElementById('compute').addEventListener('click', () => {
  output.textContent = computePairs(nameInput.value);
});

nameInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    e.preventDefault();
    document.getElementById('compute').click();
  }
});

const toggleBtn = document.getElementById('themeToggle');

// load saved theme
if (localStorage.getItem('theme') === 'dark') {
  document.body.classList.add('dark');
  toggleBtn.textContent = '☀️ Light';
}

toggleBtn.addEventListener('click', () => {
  document.body.classList.toggle('dark');

  const isDark = document.body.classList.contains('dark');
  toggleBtn.textContent = isDark ? '☀️ Light' : '🌙 Dark';
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
});


