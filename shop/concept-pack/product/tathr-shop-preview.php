<?php
/**
 * Plugin Name: TATHR 商店预览模式
 * Description: 暂不收款时使用：商品可看不可买，购物车和结账页跳回商品页，购买按钮换成「开售通知」表单和免费试读。名单在后台「开售通知名单」里。开始收款时删除本文件即可。
 * Version: 1.0
 *
 * 放在 wp-content/mu-plugins/ 下，自动生效，无需在后台启用。
 */

if (!defined('ABSPATH')) {
    exit;
}

const TATHR_SAMPLE_URL = '/wp-content/uploads/tathr/tathr-card-01-sample.pdf';

// 1. 所有商品都不可购买：前台不出现「加入购物车」。
add_filter('woocommerce_is_purchasable', '__return_false');

// 价格后面标注「即将开售」。
add_filter('woocommerce_get_price_html', function ($html) {
    return $html ? $html . ' <span class="tathr-soon">· 即将开售</span>' : $html;
});

// 2. 购物车、结账页一律跳回商店首页。
add_action('template_redirect', function () {
    if (function_exists('is_cart') && (is_cart() || is_checkout())) {
        wp_safe_redirect(wc_get_page_permalink('shop'));
        exit;
    }
});

// 3. 开售通知名单：一个后台可见、前台不公开的文章类型，每个邮箱一条。
add_action('init', function () {
    register_post_type('tathr_waitlist', [
        'labels' => ['name' => '开售通知名单', 'singular_name' => '开售通知', 'menu_name' => '开售通知名单'],
        'public' => false,
        'show_ui' => true,
        'show_in_menu' => true,
        'menu_icon' => 'dashicons-email-alt',
        'supports' => ['title'],
        'capability_type' => 'post',
        'capabilities' => ['create_posts' => 'do_not_allow'],
        'map_meta_cap' => true,
    ]);
});

add_filter('manage_tathr_waitlist_posts_columns', function ($cols) {
    return ['cb' => $cols['cb'], 'title' => '邮箱', 'product' => '来自商品', 'date' => '时间'];
});
add_action('manage_tathr_waitlist_posts_custom_column', function ($col, $id) {
    if ($col === 'product') {
        $pid = (int) get_post_meta($id, '_product_id', true);
        echo $pid ? esc_html(get_the_title($pid)) : '—';
    }
}, 10, 2);

function tathr_handle_notify()
{
    $back = wp_get_referer() ?: home_url('/');
    $back = remove_query_arg('notify', $back);

    if (!isset($_POST['_tathr']) || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['_tathr'])), 'tathr_notify')) {
        wp_safe_redirect(add_query_arg('notify', 'err', $back) . '#tathr-notify');
        exit;
    }
    // 蜜罐：机器人会填这个隐藏字段。
    if (!empty($_POST['website'])) {
        wp_safe_redirect(add_query_arg('notify', 'ok', $back) . '#tathr-notify');
        exit;
    }
    $email = sanitize_email(wp_unslash($_POST['email'] ?? ''));
    if (!is_email($email)) {
        wp_safe_redirect(add_query_arg('notify', 'bad', $back) . '#tathr-notify');
        exit;
    }
    $email = strtolower($email);
    $exists = get_posts(['post_type' => 'tathr_waitlist', 'title' => $email, 'post_status' => 'any', 'fields' => 'ids', 'numberposts' => 1]);
    if (!$exists) {
        $id = wp_insert_post(['post_type' => 'tathr_waitlist', 'post_title' => $email, 'post_status' => 'private']);
        if ($id && !is_wp_error($id)) {
            update_post_meta($id, '_product_id', absint($_POST['product_id'] ?? 0));
        }
    }
    wp_safe_redirect(add_query_arg('notify', 'ok', $back) . '#tathr-notify');
    exit;
}
add_action('admin_post_nopriv_tathr_notify', 'tathr_handle_notify');
add_action('admin_post_tathr_notify', 'tathr_handle_notify');

// 4. 商品页上的「即将开售」卡片：替代原来的购买按钮。
function tathr_notify_box()
{
    static $done = false;
    if ($done || !function_exists('is_product') || !is_product()) {
        return '';
    }
    $done = true;

    $state = sanitize_key($_GET['notify'] ?? '');
    $msg = [
        'ok' => '<p class="tathr-msg ok">已记下，开售当天会发邮件通知你。</p>',
        'bad' => '<p class="tathr-msg">邮箱格式不太对，再试一次？</p>',
        'err' => '<p class="tathr-msg">页面过期了，刷新后再提交一次。</p>',
    ][$state] ?? '';

    ob_start(); ?>
<div class="tathr-box" id="tathr-notify">
  <p class="tathr-h">即将开售</p>
  <p>留下邮箱，开售当天通知你。现在可以先免费下载第 1 张「神经网络」，看看合不合适。</p>
  <p><a class="tathr-sample" href="<?php echo esc_url(TATHR_SAMPLE_URL); ?>" download>免费下载第 1 张（PDF）↓</a></p>
  <?php echo $msg; ?>
  <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
    <input type="hidden" name="action" value="tathr_notify">
    <input type="hidden" name="product_id" value="<?php echo esc_attr(get_the_ID()); ?>">
    <?php wp_nonce_field('tathr_notify', '_tathr', false); ?>
    <input type="text" name="website" tabindex="-1" autocomplete="off" class="tathr-hp" aria-hidden="true">
    <input type="email" name="email" required placeholder="你的邮箱" aria-label="你的邮箱">
    <button type="submit">开售通知我</button>
  </form>
  <p class="tathr-fine">邮箱只用于这一次开售通知，不会给第三方，想删除随时告诉我们。</p>
</div>
<?php
    return ob_get_clean();
}

// 经典主题：放在原来「加入购物车」的位置。
add_action('woocommerce_single_product_summary', function () {
    echo tathr_notify_box();
}, 30);

// 区块主题：替换「加入购物车」表单区块的位置。
add_filter('render_block', function ($content, $block) {
    $names = ['woocommerce/add-to-cart-form', 'woocommerce/add-to-cart-with-options'];
    if (in_array($block['blockName'] ?? '', $names, true)) {
        return tathr_notify_box();
    }
    return $content;
}, 10, 2);

add_action('wp_head', function () { ?>
<style>
.tathr-soon{color:#ff6a3d;font-size:.85em}
.tathr-box{margin:1.5em 0;padding:1.25em 1.4em;border:1px solid #16150f;background:#f6f2e9;color:#16150f;max-width:34em}
.tathr-box .tathr-h{font-weight:700;font-size:1.15em;color:#ff6a3d;margin:0 0 .4em}
.tathr-box p{margin:.4em 0}
.tathr-sample{color:#16150f;font-weight:600}
.tathr-box form{display:flex;gap:.5em;flex-wrap:wrap;margin-top:.8em}
.tathr-box input[type=email]{flex:1 1 14em;padding:.6em .7em;border:1px solid #16150f;background:#fff;font-size:1em}
.tathr-box button{padding:.6em 1.1em;border:0;background:#16150f;color:#f6f2e9;font-size:1em;cursor:pointer}
.tathr-box button:hover{background:#ff6a3d}
.tathr-hp{position:absolute;left:-9999px;width:1px;height:1px;opacity:0}
.tathr-msg{padding:.4em .6em;background:#fff;border-left:3px solid #ff6a3d}
.tathr-msg.ok{border-color:#2f7d32}
.tathr-fine{font-size:.8em;color:#8f8a7d}
</style>
<?php });
