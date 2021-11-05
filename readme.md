### SNH48商城抢票脚本

使用前需在`config.yml`配置个人信息（用于登录和验证）

- `username`: 用户名
- `password`: 密码
- `nick_name`：昵称
- `ticket_type`：门票种类, 最多可写3项，表示抢票顺序
  - 1：VIP门票
  - 2：普通门票
  - 3：站票

> 例：[2, 1, 3]，表示抢票优先级:普通门票>VIP门票>站票

- `ticket_num`: 抢票数量

> 由于大多门票有限制，建议提前了解再填写

- `target_url`: 抢票地址
- `driver_path`: `chromedriver`路径
- `index_url`: 主页（一般不修改）

> 注意：`YAML`文件数据冒号后需留一个空格
> chromedriver 注意与自己Chrome浏览器版本一致



填写后运行脚本，目前抢到后会默认选择使用支付宝支付，直接跳转到付款码界面

之后会将付款码发送至微信提醒付款