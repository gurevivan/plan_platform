import json
import re
from pathlib import Path

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import PlanState

PLAN_KEY = 'prod-plan-v6'
PLAN_FILE = Path(__file__).resolve().parent.parent / 'Plan.html'

# Перехватывает localStorage.setItem и отправляет данные на сервер после каждого сохранения
SAVE_HOOK = """<script>
(function(){
  var _orig = Storage.prototype.setItem;
  Storage.prototype.setItem = function(k, v) {
    _orig.call(this, k, v);
    if (k === 'prod-plan-v6') {
      fetch('/api/save', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({key: k, value: v})
      }).catch(console.error);
    }
  };
})();
</script>"""


def index(request):
    html = PLAN_FILE.read_text(encoding='utf-8')

    try:
        state = PlanState.objects.get(key=PLAN_KEY)
        preload_value = state.value
    except PlanState.DoesNotExist:
        preload_value = ''

    # Вставляем текущие данные прямо в страницу — никакого дополнительного запроса не нужно
    if preload_value:
        data_json = json.dumps(preload_value).replace('</', '<\\/')
        preload = f"<script>localStorage.setItem('prod-plan-v6', {data_json});</script>"
    else:
        preload = ''

    html = re.sub(
        r'</head>',
        preload + SAVE_HOOK + '</head>',
        html, count=1, flags=re.IGNORECASE
    )
    return HttpResponse(html, content_type='text/html; charset=utf-8')


@csrf_exempt
def api_save(request):
    if request.method != 'POST':
        return HttpResponse(status=405)
    data = json.loads(request.body)
    PlanState.objects.update_or_create(
        key=data['key'],
        defaults={'value': data['value']}
    )
    return HttpResponse('ok')
