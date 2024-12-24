import subprocess
import re
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

# Telegram API Token
TELEGRAM_API_TOKEN = '填写你的机器人api'

# 单位转换
UNIT_CONVERSIONS = {
    'b': 1,
    'K': 1e3,
    'M': 1e6,
    'G': 1e9,
    'T': 1e12
}

def convert_to_float(value_with_unit):
    """Convert a string like '2.11K' to a float value (2.11 * 1000) and return the value with the unit."""
    if not value_with_unit:
        return None, None
    
    match = re.match(r"([0-9\.]+)([a-zA-Z]+)", value_with_unit)
    if match:
        value = float(match.group(1))
        unit = match.group(2).upper()
        if unit in UNIT_CONVERSIONS:
            return value * UNIT_CONVERSIONS[unit], unit
    return None, None

# 使用 subprocess 调用 iftop 并获取输出
def get_iftop_data():
    """获取 iftop 的输出并提取网络速率数据"""
    result = subprocess.run(['sudo', 'iftop', '-t', '-s', '1', '-L', '10'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stdout.decode()

    # 调整正则表达式，以确保提取所有数据
    receive_rate_match = re.search(r"Total receive rate:\s+(\d+\.\d+[\w]+)", output)
    peak_rate_match = re.search(r"Peak rate \(sent/received/total\):\s+([\d\.]+[\w]+)\s+([\d\.]+[\w]+)\s+([\d\.]+[\w]+)", output)

    receive_rate = peak_sent = peak_received = peak_total = None
    if receive_rate_match:
        receive_rate = receive_rate_match.group(1)
    
    if peak_rate_match:
        peak_sent = peak_rate_match.group(1)
        peak_received = peak_rate_match.group(2)
        peak_total = peak_rate_match.group(3)
    
    return receive_rate, peak_sent, peak_received, peak_total

# 欢迎信息和总菜单按钮
async def start(update: Update, context: CallbackContext):
    """总菜单和子菜单按钮"""
    # 总菜单
    keyboard = [
        [InlineKeyboardButton("服务器管理", callback_data='server_menu')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text('欢迎使用网络监控系统，请选择操作:', reply_markup=reply_markup)

# 处理总菜单按钮点击事件
async def button_click(update: Update, context: CallbackContext):
    """按钮点击后处理"""
    query = update.callback_query
    await query.answer()  # 确认按钮点击

    # 如果点击的是“服务器管理”按钮，显示子菜单
    if query.data == 'server_menu':
        keyboard = [
            [InlineKeyboardButton("服务器1", callback_data='server1')],
            [InlineKeyboardButton("返回主菜单", callback_data='back_to_main')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="请选择操作:", reply_markup=reply_markup)

    # 判断是否点击了“服务器1”按钮
    elif query.data == 'server1':
        await handle_server1_query(query, context)

    # 返回主菜单，并停止推送
    elif query.data == 'back_to_main' or query.data == 'back_to_main_and_stop':
        # 停止当前推送任务并返回菜单
        await stop_current_task(context)
        await start(update, context)

# 处理服务器1的按钮点击
async def handle_server1_query(query, context):
    """处理服务器1的网络监控和测试"""
    # 获取 iftop 数据
    receive_rate, peak_sent, peak_received, peak_total = get_iftop_data()

    # 显示初始网络信息
    message = f"""服务器1：
IP: 168.75.95.125
端口: 80
本信息持续推送

接收总速率: {receive_rate if receive_rate else '无数据'}
峰值发送速率: {peak_sent if peak_sent else '无数据'}
峰值接收速率: {peak_received if peak_received else '无数据'}
峰值总速率: {peak_total if peak_total else '无数据'}"""
        
    # 启动持续推送
    await query.edit_message_text(text=message)
    await start_attack_test(query, context)

# 启动攻击测试并持续推送数据
async def start_attack_test(query, context):
    """开始攻击测试并持续推送数据"""
    # 如果已经有任务在运行，直接返回
    if 'push_task' in context.chat_data and not context.chat_data['push_task'].done():
        await query.edit_message_text(text="监控任务已经在运行中，请稍后再试。")
        return

    # 标记服务器1为占用状态
    context.chat_data['server1_occupied'] = True
    context.chat_data['stop_attack'] = False  # 初始化停止标志为 False

    # 创建按钮，包含停止推送和返回主菜单功能
    keyboard = [
        [InlineKeyboardButton("停止测试推送", callback_data='back_to_main_and_stop')],
        [InlineKeyboardButton("返回到服务器管理主菜单", callback_data='server_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # 推送开始
    stop_event = asyncio.Event()
    context.chat_data['stop_event'] = stop_event

    # 启动推送数据任务
    async def push_network_data():
        try:
            # 设置计时器为90秒后停止推送
            timeout = 90  # 90秒
            start_time = asyncio.get_event_loop().time()

            while not stop_event.is_set():
                # 检查是否超过90秒
                if asyncio.get_event_loop().time() - start_time > timeout:
                    break  # 超过90秒，停止推送

                # 获取 iftop 数据
                receive_rate, peak_sent, peak_received, peak_total = get_iftop_data()

                message = (f"服务器1：\n"
                           f"IP: 168.75.95.125\n"
                           f"端口: 80 持续90秒推送\n\n"
                           f"接收总速率: {receive_rate if receive_rate else '无数据'}\n"
                           f"峰值发送速率: {peak_sent if peak_sent else '无数据'}\n"
                           f"峰值接收速率: {peak_received if peak_received else '无数据'}\n"
                           f"峰值总速率: {peak_total if peak_total else '无数据'}")

                # 每次发送一条新消息
                await query.message.reply_text(text=message, reply_markup=reply_markup)
                
                await asyncio.sleep(1)  # 减少等待时间，让按钮事件更快响应
        except asyncio.CancelledError:
            pass

    # 启动异步任务
    context.chat_data['push_task'] = asyncio.create_task(push_network_data())

# 停止当前推送任务
async def stop_current_task(context):
    """停止当前的推送任务"""
    if 'push_task' in context.chat_data:
        # 设置停止事件
        stop_event = context.chat_data.get('stop_event')
        if stop_event:
            stop_event.set()

        # 确保任务取消
        task = context.chat_data['push_task']
        if not task.done():
            task.cancel()
            await task

    context.chat_data['server1_occupied'] = False  # 释放占用

# 创建应用实例并添加处理器
def main():
    """启动机器人并添加处理器"""
    application = Application.builder().token(TELEGRAM_API_TOKEN).build()

    # 添加命令和按钮处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))

    # 启动应用
    application.run_polling()

if __name__ == '__main__':
    main()
