>Telebot
How it works ?

1. User start chat with /start command.
2. If user unlock account write in chat phone number where AD mobile phone.
3. Api send OTP code SMS.
4. User write chat bot `unlock mobile_number OTP`.
5. If you wanna reset password `reset mobile_number OTP new_password`.

> Security solutions:
```
3 times false OTP OTP expired (telegram user blocked)
OTP expired time 3 minute
3 time unlock 1 hour (after that block user number and telegram_id)
```
> Chart
![workflow]([https://github.com/murad9911/telebot/blob/main/tele.html](https://github.com/murad9911/telebot/blob/main/workflow.png?raw=true)

