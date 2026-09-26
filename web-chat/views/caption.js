// Gradio의 대화 기록 변경 콜백. 장면이 있는 화면에서만 등록된다.
// iframe을 새로 불러오지 않고 부모 웹의 자막만 갱신한다.
(history) => {
    const caption = document.querySelector('[data-caption]');
    const reply = history.findLast(message => message.role === 'assistant');

    // 응답 대기 중에는 직전 답변을 유지한다. 기록을 지우면 첫 인사로 돌아간다.
    let text = caption.dataset.opening;
    if (reply) {
        // Gradio 본문은 문자열 또는 콘텐츠 블록 목록이므로 텍스트만 추출한다.
        text = typeof reply.content === 'string'
            ? reply.content
            : reply.content.filter(block => block.type === 'text').map(block => block.text).join('');
    }

    // 모델 답변을 HTML로 실행하지 않고 일반 텍스트로 표시한다.
    caption.textContent = text;
    caption.scrollTop = 0;
}
