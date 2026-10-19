# 交接：shop.tathr.com 上线（展示 + 开售通知，暂不收款）

给负责服务器的线程（经 nono Mac 上的会话 `ssh tathr` 操作）。nono 的要求（2026-10-19）：**商店页面上线，但暂时不做收款**。
所以：装 WooCommerce、上架商品，但**不装任何支付插件**；购买按钮换成「开售通知」邮箱表单 + 免费试读第 1 张；购物车和结账页跳回商店。

## 0. 拿到文件

文件都在 GitHub 仓库 `nfau59/nfau59` 的 `claude/project-thread-30f1eg` 分支，目录 `shop/concept-pack/`（云端的 /mnt/project-files 在 Mac 上读不到，所以走 GitHub）。在 Mac 上：

```bash
git clone --depth 1 -b claude/project-thread-30f1eg https://github.com/nfau59/nfau59 ~/Documents/tathr-shop-pack
P=~/Documents/tathr-shop-pack/shop/concept-pack
ssh tathr 'mkdir -p /tmp/cards'
scp $P/dist/*.pdf $P/dist/preview-*.png $P/product/product-description.html \
    $P/product/tathr-card-01-sample.pdf $P/product/tathr-shop-preview.php tathr:/tmp/cards/
```
PDF 不用在 Mac 上重新生成，`dist/` 里就是成品（文件名都是英文，避免 URL 编码问题）。

## 1. 装 wp-cli（在 shop 容器里，继承容器的数据库环境变量）

```bash
cd ~/tathr-server
docker compose exec shop bash -c 'curl -sSLo /usr/local/bin/wp https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar && chmod +x /usr/local/bin/wp'
WP() { docker compose exec -T -u www-data shop wp "$@"; }
WP core version && WP user list --role=administrator --fields=ID,user_login
WP theme list --status=active
```
记下管理员登录名（下面写作 `ADMIN`）和当前主题。

## 2. 装并配置 WooCommerce（不装支付插件）

```bash
WP plugin install woocommerce --activate
WP option update woocommerce_currency USD
WP option update woocommerce_default_country CN
WP option update woocommerce_calc_taxes no
WP option update woocommerce_ship_to_countries disabled
WP option update woocommerce_file_download_method force
WP option update woocommerce_coming_soon no          # 关掉 Woo 自带的「即将上线」整站遮罩，页面要能公开访问
WP option update woocommerce_store_pages_only no
WP wc tool run install_pages --user=ADMIN
# 商店页设为首页：打开 shop.tathr.com 直接看到商品
SHOP_ID=$(WP option get woocommerce_shop_page_id)
WP option update show_on_front page && WP option update page_on_front $SHOP_ID
WP option update blogname "TATHR 商店" && WP option update blogdescription "概念显影 · 图解卡"
```
**不要**装 woocommerce-paypal-payments 或任何收款插件；付款方式保持全部关闭。

## 3. 装预览模式插件（核心）

```bash
CID=$(docker compose ps -q shop)
docker exec $CID mkdir -p /var/www/html/wp-content/mu-plugins
docker cp /tmp/cards/tathr-shop-preview.php $CID:/var/www/html/wp-content/mu-plugins/
docker exec $CID chown -R www-data:www-data /var/www/html/wp-content/mu-plugins
```
它做的事：所有商品不可购买（价格后标「· 即将开售」）；商品页原「加入购物车」位置换成卡片：免费下载第 1 张 + 邮箱表单「开售通知我」；购物车 / 结账页 302 回商店首页；邮箱存到后台左侧菜单「开售通知名单」（不公开）。
**回滚**：删掉这个文件即可，网站立即恢复 Woo 默认行为。

## 4. 上传文件

```bash
# 免费试读：公开目录
docker exec $CID mkdir -p /var/www/html/wp-content/uploads/tathr
docker cp /tmp/cards/tathr-card-01-sample.pdf $CID:/var/www/html/wp-content/uploads/tathr/
# 正式文件：受保护目录（以后开售用）
docker exec $CID mkdir -p /var/www/html/wp-content/uploads/woocommerce_uploads/tathr
for f in /tmp/cards/tathr-c*.pdf; do docker cp "$f" $CID:/var/www/html/wp-content/uploads/woocommerce_uploads/tathr/; done
docker exec $CID rm -f /var/www/html/wp-content/uploads/woocommerce_uploads/tathr/tathr-card-01-sample.pdf
docker exec $CID chown -R www-data:www-data /var/www/html/wp-content/uploads
for f in /tmp/cards/preview-*.png /tmp/cards/product-description.html; do docker cp "$f" $CID:/tmp/; done
COVER=$(WP media import /tmp/preview-cover.png --porcelain)
GALLERY=$(for i in 1 2 3 4 5 6; do WP media import /tmp/preview-0$i.png --porcelain; done | tr '\n' ' ')
echo $COVER $GALLERY
```

## 5. 建商品

```bash
U=https://shop.tathr.com/wp-content/uploads/woocommerce_uploads/tathr
IMGS="[{\"id\":$COVER}$(for g in $GALLERY; do printf ',{"id":%s}' $g; done)]"
WP wc product create --user=ADMIN \
  --name="概念显影 · 图解卡 第一辑（6 张 A4 可打印 PDF）" \
  --slug=concept-cards-vol1 --sku=TATHR-CC-V1 --type=simple --status=publish \
  --regular_price=9 --virtual=true --downloadable=true \
  --short_description="神经网络、区块链、复利、时空弯曲、傅里叶变换、熵：每个概念一张卡，一句话定义 + 一个日常类比 + 对照表，扫码还能拨动 3D 模型。" \
  --description="$(docker compose exec -T shop cat /tmp/product-description.html)" \
  --images="$IMGS" \
  --downloads="[
    {\"name\":\"合集（8 页）\",\"file\":\"$U/tathr-concept-cards-vol1.pdf\"},
    {\"name\":\"01 神经网络\",\"file\":\"$U/tathr-card-01-neural-network.pdf\"},
    {\"name\":\"02 区块链\",\"file\":\"$U/tathr-card-02-blockchain.pdf\"},
    {\"name\":\"03 复利\",\"file\":\"$U/tathr-card-03-compound-interest.pdf\"},
    {\"name\":\"04 时空弯曲\",\"file\":\"$U/tathr-card-04-curved-spacetime.pdf\"},
    {\"name\":\"05 傅里叶变换\",\"file\":\"$U/tathr-card-05-fourier-transform.pdf\"},
    {\"name\":\"06 熵\",\"file\":\"$U/tathr-card-06-entropy.pdf\"}]"
WP rewrite flush
```

## 6. 主站加入口

在 nono 的 Mac 上：
```bash
python3 $P/product/add-buy-links.py ~/Documents/tathr-sites/concept   # 幂等，可重复运行
```
效果：6 个概念面板各多一个「图解卡即将开售 · 先免费看第 1 张 →」链接，结尾按钮组多一个「图解卡 · 即将开售 ↗」，都指向 `https://shop.tathr.com/product/concept-cards-vol1/`（带 utm 参数）。然后按原来的方式把 concept 目录部署到服务器。

## 7. 验证（全部通过才算上线）

- `https://shop.tathr.com/` 显示商店，有这一个商品，价格「$9.00 · 即将开售」。
- 商品页：没有「加入购物车」按钮；有「即将开售」卡片、免费下载链接、邮箱表单。**如果卡片没出现**（区块主题的模板不同），把主题换成经典主题 Storefront：`WP theme install storefront --activate`，再看一次。
- 用一个测试邮箱提交表单 → 页面显示「已记下」→ 后台「开售通知名单」里出现这条；验证后删掉测试条目。
- `https://shop.tathr.com/cart/`、`/checkout/` 都 302 跳回首页。
- `https://shop.tathr.com/wp-content/uploads/tathr/tathr-card-01-sample.pdf` 能下载（200）。
- `$U/tathr-concept-cards-vol1.pdf` 直接访问被拒（403），不能绕过。
- 后台 WooCommerce → 设置 → 付款：所有付款方式都是关闭状态。
- tathr.com 每个概念面板底部有橙色链接，点击跳到商品页。

## 以后开始收款时

1. 删除 `wp-content/mu-plugins/tathr-shop-preview.php`；
2. 装 woocommerce-paypal-payments，由 nono 本人在后台登录 PayPal 授权；
3. 接 SMTP 发信插件，确保买家能收到下载邮件；
4. 把主站链接文字改回「下载这张图解卡」，并给「开售通知名单」里的邮箱发开售通知。
