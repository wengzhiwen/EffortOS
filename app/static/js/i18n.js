// i18n — 前端国际化模块
// 依赖：页面模板注入 window.__i18n_dict 和 window.__i18n_lang
(function() {
    var dict = window.__i18n_dict || {};
    var currentLang = window.__i18n_lang || 'zh_CN';

    function getNestedValue(obj, key) {
        var parts = key.split('.');
        var cur = obj;
        for (var i = 0; i < parts.length; i++) {
            if (cur && typeof cur === 'object' && parts[i] in cur) {
                cur = cur[parts[i]];
            } else {
                return null;
            }
        }
        return cur;
    }

    window.t = function(key, params) {
        var value = getNestedValue(dict, key);
        if (value === null) return key;
        if (params && typeof value === 'string') {
            return value.replace(/\{(\w+)\}/g, function(_, k) {
                return params[k] !== undefined ? params[k] : '{' + k + '}';
            });
        }
        return value;
    };

    window.getCurrentLang = function() { return currentLang; };

    window.switchLang = function(lang) {
        document.cookie = 'lang=' + lang + ';path=/;max-age=' + (365 * 86400);
        window.location.reload();
    };

    // 填充全局 TYPE_NAMES
    window.TYPE_NAMES = {
        cycling: t('types.cycling'),
        indoor_cycling: t('types.indoor_cycling'),
        commute_cycling: t('types.commute_cycling'),
        running: t('types.running'),
        indoor_running: t('types.indoor_running'),
        walking: t('types.walking'),
        swimming: t('types.swimming'),
        other: t('types.other')
    };
})();
