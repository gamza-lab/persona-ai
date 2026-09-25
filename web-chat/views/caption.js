(history) => {
    const stage = document.querySelector('[data-persona-stage]');
    if (!stage) return;
    const last = history?.[history.length - 1];
    let text = '';
    if (last?.role === 'assistant') {
        text = typeof last.content === 'string' ? last.content :
            (last.content || []).filter(b => b.type === 'text').map(b => b.text).join('');
    }
    stage.dispatchEvent(new CustomEvent('persona-caption', {
        detail: {text, pending: last?.role === 'user', empty: !history?.length}
    }));
}
