# 大麦 App 抢票自动化

基于 Appium + UiAutomator2 的大麦 APP 抢票脚本。运行前需手动打开大麦 APP，进入目标演出详情页。

## 快速开始

```bash
# 1. 启动 Appium 服务
./start_appium.sh

# 2. 编辑 damai_appium/config.jsonc 配置目标演出、票价等

# 3. 打开大麦 APP，进入演出详情页

# 4. 运行抢票
./start_ticket_grabbing.sh
```

## 配置说明 (config.jsonc)

### 必填参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `server_url` | string | Appium 服务地址，通常为 `http://127.0.0.1:4723` |
| `keyword` | string | 演出关键词（用于日志/展示，当前流程不参与搜索） |
| `users` | array | 观演人列表（用于日志/展示，当前流程不参与选择） |
| `city` | string | 城市（用于日志/展示，当前流程不参与选择） |
| `date` | string 或 array | 场次日期，如 `"04.19"` 或 `["04.19","04.20"]`，按顺序尝试匹配；不配置或空则跳过场次选择 |
| `price_indices` | array | 票价索引，如 `[0, 1]` 表示优先点第 0 个，其次第 1 个；会跳过缺货/售罄项 |
| `if_commit_order` | boolean | 是否点击「提交订单」；`false` 时只选票价、确定购买，不提交 |

### 重试与节奏

| 参数 | 类型 | 说明 |
|------|------|------|
| `max_retries` | number | 整轮抢票最大重试次数，失败后返回上一页再重试 |
| `retry_interval_sec` | number | 每次重试间隔（秒） |
| `reinit_driver_on_retry` | boolean | 重试时是否重新初始化 Appium 驱动 |

### 等待与点击超时

| 参数 | 类型 | 说明 |
|------|------|------|
| `default_wait_sec` | number | WebDriver 默认等待超时（秒） |
| `fast_click_timeout_sec` | number | 快速点击（如确定购买）的等待超时 |
| `smart_click_timeout_sec` | number | 智能点击（多选择器兜底）的等待超时 |
| `smart_click_poll_frequency_sec` | number | WebDriverWait 轮询间隔（秒），默认 0.02，越小检测越快 |
| `user_find_timeout_sec` | number | 用户选择相关超时（当前流程未使用） |
| `user_fuzzy_timeout_sec` | number | 用户模糊匹配超时（当前流程未使用） |

### 预约/购买入口轮询

| 参数 | 类型 | 说明 |
|------|------|------|
| `book_poll_timeout_sec` | number | 等待「预约/购买」按钮可点击的总超时（秒） |
| `book_poll_interval_sec` | number | 轮询间隔（秒） |
| `book_entry_timeout_sec` | number | 单次尝试点击预约入口的等待超时（秒） |

### 场次选择

| 参数 | 类型 | 说明 |
|------|------|------|
| `date_select_timeout_sec` | number | 场次日期点击的等待超时（秒） |

### 票价选择

| 参数 | 类型 | 说明 |
|------|------|------|
| `price_candidate_wait_sec` | number | 等待票价容器就绪的超时（秒） |
| `price_container_poll_interval_sec` | number | 等待票价容器时的轮询间隔（秒） |
| `price_click_duration_ms` | number | 票价项点击手势时长（毫秒） |
| `price_soldout_poll_max` | number | 票价缺货时原地刷新轮询次数，超时后再返回上一页 |
| `price_soldout_poll_interval_sec` | number | 每次刷新后等待秒数，再尝试选票 |

### 返回上一页

| 参数 | 类型 | 说明 |
|------|------|------|
| `go_back_wait_sec` | number | 票价未命中时 driver.back() 后的等待（秒） |
| `go_back_key_wait_sec` | number | 按返回键后的等待（秒） |

### 点击手势

| 参数 | 类型 | 说明 |
|------|------|------|
| `click_gesture_duration_ms` | number | 通用点击手势时长（毫秒），用于弹窗、确定购买等 |

### 确定购买

| 参数 | 类型 | 说明 |
|------|------|------|
| `confirm_buy_timeout_sec` | number | 确定购买按钮的等待超时（秒） |
| `confirm_buy_wait_sec` | number | 点击确定购买后的等待（秒） |

### 提交订单弹窗

| 参数 | 类型 | 说明 |
|------|------|------|
| `order_modal_retry_max` | number | 遇「同一时间下单人数过多」弹窗时的最大重试次数 |
| `order_modal_retry_wait_sec` | number | 点击「继续尝试」后等待秒数，再尝试提交 |
| `order_submit_timeout_sec` | number | 提交按钮的等待超时（秒） |
| `order_submit_click_wait_sec` | number | 点击提交按钮后、检查弹窗前等待（秒） |

### 其他

| 参数 | 类型 | 说明 |
|------|------|------|
| `skip_city_selection` | boolean | 是否跳过城市选择（当前流程未使用） |
| `batch_click_delay_sec` | number | 批量点击间隔（当前流程未使用） |
| `quantity_click_delay_sec` | number | 数量点击间隔（当前流程未使用） |
| `post_run_sleep_sec` | number | 抢票流程结束后的等待秒数 |

## 配置示例

```jsonc
{
  "server_url": "http://127.0.0.1:4723",
  "keyword": "张杰",
  "users": ["梁涛"],
  "city": "北京",
  "date": "04.19",
  "price_indices": [0, 1],
  "if_commit_order": true,
  "max_retries": 5000,
  "retry_interval_sec": 0.1,
  "reinit_driver_on_retry": false,
  "default_wait_sec": 0.35,
  "fast_click_timeout_sec": 0.3,
  "smart_click_timeout_sec": 0.3,
  "book_entry_timeout_sec": 0.25,
  "date_select_timeout_sec": 0.3,
  "price_container_poll_interval_sec": 0.02,
  "price_click_duration_ms": 25,
  "price_soldout_poll_max": 5,
  "price_soldout_poll_interval_sec": 0.1,
  "go_back_wait_sec": 0.12,
  "go_back_key_wait_sec": 0.1,
  "click_gesture_duration_ms": 50,
  "confirm_buy_timeout_sec": 0.35,
  "confirm_buy_wait_sec": 0.15,
  "order_modal_retry_max": 10,
  "order_modal_retry_wait_sec": 0.1,
  "order_submit_timeout_sec": 0.35,
  "order_submit_click_wait_sec": 0.15,
  "post_run_sleep_sec": 0.15
}
```
