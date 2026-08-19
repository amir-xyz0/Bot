async def chat_with_past_self(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (قسمت‌های قبلی) ...

    try:
        url = f"{config.OPENROUTER_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://t.me/your_bot",
            "X-Title": "Life Assistant Bot"
        }
        payload = {
            "model": config.OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.85,
            "max_tokens": 450
        }

        logger.info(f"📤 ارسال به OpenRouter (past_self): {json.dumps(payload, ensure_ascii=False)[:200]}...")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response_data = response.json()
        
        logger.info(f"📥 وضعیت OpenRouter (past_self): {response.status_code}")
        logger.info(f"📄 پاسخ OpenRouter (past_self): {json.dumps(response_data, ensure_ascii=False)[:500]}...")

        if response.status_code == 200:
            reply = response_data.get("choices", [{}])[0].get("message", {}).get("content")
            if reply:
                await update.message.reply_text(f"🕰️ **همراه گذشته:**\n\n{reply}")
                db.close()
                return
            else:
                logger.warning("⚠️ پاسخ خالی از OpenRouter (past_self)")
        else:
            error_msg = response_data.get("error", {}).get("message", "خطای ناشناخته")
            logger.error(f"❌ خطای OpenRouter (past_self): {error_msg}")
            
    except Exception as e:
        logger.error(f"❌ خطا در گفتگوی گذشته: {e}")
    
    # ... (بقیه کد)
