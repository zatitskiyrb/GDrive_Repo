/** v2 — inline keyboard, per-country location presets
 * Cloudflare Workers — Telegram webhook handler for HR Scraper bot.
 *
 * Environment variables (Cloudflare dashboard → Workers → Settings → Variables):
 *   TELEGRAM_TOKEN   — bot token from @BotFather
 *   GITHUB_TOKEN     — GitHub Personal Access Token (repo scope)
 *   GITHUB_REPO      — e.g. "zatitskiyrb/GDrive_Repo"
 *   ALLOWED_CHAT_ID  — your Telegram chat ID (bot ignores everyone else)
 */

const LOCATION_KEYBOARD = {
  inline_keyboard: [
    [
      { text: "🌍 Europe",         callback_data: "loc:Europe" },
      { text: "🏔 Scandinavia",    callback_data: "loc:Scandinavia" },
    ],
    [
      { text: "🌊 Baltic",         callback_data: "loc:Baltic" },
      { text: "🏙 Eastern Europe", callback_data: "loc:Eastern Europe" },
    ],
    [
      { text: "🌐 Remote (world)", callback_data: "loc:Remote" },
    ],
  ],
};

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

    // --- Handle inline button press ---
    if (body?.callback_query) {
      const cb = body.callback_query;
      const chatId = String(cb.message.chat.id);
      const data = cb.data || "";

      if (env.ALLOWED_CHAT_ID && chatId !== env.ALLOWED_CHAT_ID) {
        await answerCallback(env, cb.id);
        return new Response("OK");
      }

      if (data.startsWith("loc:")) {
        const location = data.replace("loc:", "");
        await answerCallback(env, cb.id, `Запускаю: ${location}`);
        await editMessage(env, chatId, cb.message.message_id,
          `🚀 Запускаю поиск...\n📍 Локация: *${location}*\n\nПришлю результат когда закончу (~5 мин).`
        );
        const ok = await triggerActions(env, location, chatId);
        if (!ok) {
          await sendMessage(env, chatId, "❌ Не удалось запустить GitHub Actions. Проверь токен.");
        }
      }
      return new Response("OK");
    }

    // --- Handle text commands ---
    const message = body?.message;
    if (!message) return new Response("OK");

    const chatId = String(message.chat.id);
    const text = (message.text || "").trim();

    if (env.ALLOWED_CHAT_ID && chatId !== env.ALLOWED_CHAT_ID) {
      return new Response("OK");
    }

    if (text === "/start" || text === "/help") {
      await sendMessage(env, chatId, "Выбери регион поиска:", false, LOCATION_KEYBOARD);

    } else if (text === "/run") {
      await sendMessage(env, chatId, "Выбери регион поиска:", false, LOCATION_KEYBOARD);

    } else if (text.startsWith("/run ")) {
      // Поддержка ручного ввода: /run Baltic
      const location = text.replace("/run ", "").trim();
      await sendMessage(env, chatId,
        `🚀 Запускаю поиск...\n📍 Локация: *${location}*\n\nПришлю результат когда закончу (~5 мин).`, true
      );
      const ok = await triggerActions(env, location, chatId);
      if (!ok) {
        await sendMessage(env, chatId, "❌ Не удалось запустить GitHub Actions. Проверь токен.");
      }

    } else {
      await sendMessage(env, chatId, "Напиши /run чтобы запустить поиск.");
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
        inputs: { location, telegram_chat_id: chatId },
      }),
    }
  );
  return resp.status === 204;
}

async function sendMessage(env, chatId, text, markdown = false, replyMarkup = null) {
  await fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text,
      ...(markdown ? { parse_mode: "Markdown" } : {}),
      ...(replyMarkup ? { reply_markup: replyMarkup } : {}),
    }),
  });
}

async function editMessage(env, chatId, messageId, text) {
  await fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/editMessageText`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      message_id: messageId,
      text,
      parse_mode: "Markdown",
    }),
  });
}

async function answerCallback(env, callbackQueryId, text = "") {
  await fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/answerCallbackQuery`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ callback_query_id: callbackQueryId, text }),
  });
}
