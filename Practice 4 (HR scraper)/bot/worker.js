/**
 * Cloudflare Workers — Telegram webhook handler for HR Scraper bot.
 *
 * Environment variables (set in Cloudflare dashboard → Workers → Settings → Variables):
 *   TELEGRAM_TOKEN   — bot token from @BotFather
 *   GITHUB_TOKEN     — GitHub Personal Access Token (repo scope)
 *   GITHUB_REPO      — e.g. "zatitskiyrb/GDrive_Repo"
 *   ALLOWED_CHAT_ID  — your personal Telegram chat ID (security: bot responds only to you)
 */

const HELP_TEXT = `
HR Scraper Bot 🤖

Команды:
/run — запуск с настройками по умолчанию (Europe)
/run Scandinavia — Швеция, Норвегия, Дания, Финляндия
/run Baltic — Латвия, Литва, Эстония
/run Eastern Europe — Польша, Чехия, Венгрия и др.
/run Europe — вся Европа
/run Remote — удалённые по всему миру

Результат появится в Google Sheets через ~5 минут,
и я пришлю уведомление когда закончу.
`.trim();

export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("HR Scraper Bot is running.", { status: 200 });
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return new Response("Bad request", { status: 400 });
    }

    const message = body?.message;
    if (!message) return new Response("OK");

    const chatId = String(message.chat.id);
    const text = (message.text || "").trim();

    // Security: only respond to the configured chat
    if (env.ALLOWED_CHAT_ID && chatId !== env.ALLOWED_CHAT_ID) {
      return new Response("OK");
    }

    if (text === "/start" || text === "/help") {
      await sendMessage(env, chatId, HELP_TEXT);

    } else if (text.startsWith("/run")) {
      const location = text.replace("/run", "").trim() || "Europe";
      await sendMessage(env, chatId, `🚀 Запускаю поиск...\nЛокация: *${location}*\n\nПришлю результат когда закончу (~5 мин).`, true);

      const ok = await triggerActions(env, location, chatId);
      if (!ok) {
        await sendMessage(env, chatId, "❌ Не удалось запустить GitHub Actions. Проверь токен.");
      }

    } else {
      await sendMessage(env, chatId, `Не понимаю команду. Напиши /help`);
    }

    return new Response("OK");
  },
};

async function triggerActions(env, location, chatId) {
  const resp = await fetch(
    `https://api.github.com/repos/${env.GITHUB_REPO}/actions/workflows/run_scraper.yml/dispatches`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        Accept: "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "hr-scraper-bot/1.0",
      },
      body: JSON.stringify({
        ref: "main",
        inputs: {
          location: location,
          telegram_chat_id: chatId,
        },
      }),
    }
  );
  return resp.status === 204;
}

async function sendMessage(env, chatId, text, markdown = false) {
  await fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text,
      ...(markdown ? { parse_mode: "Markdown" } : {}),
    }),
  });
}
