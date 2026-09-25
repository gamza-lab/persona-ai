const stage = element.querySelector('[data-persona-stage]');
const caption = stage.querySelector('[data-caption]');
const voice = stage.querySelector('[data-voice]');
const replay = stage.querySelector('[data-replay]');
const stop = stage.querySelector('[data-stop]');
const status = stage.querySelector('[data-audio-status]');
const opening = caption.textContent;
let current = opening;
let lastReply = '';
let generation = 0;
const synth = window.speechSynthesis;
function cancel() {
    generation += 1;
    if (synth) synth.cancel();
    status.textContent = '';
}
function speak() {
    cancel();
    if (!synth || !current) return;
    const token = generation;
    const utterance = new SpeechSynthesisUtterance(current);
    utterance.lang = 'ko-KR';
    utterance.rate = 0.9;
    const korean = synth.getVoices().find(v => v.lang.startsWith('ko'));
    if (korean) utterance.voice = korean;
    utterance.onstart = () => { if (token === generation) status.textContent = '읽는 중'; };
    utterance.onend = () => { if (token === generation) status.textContent = ''; };
    utterance.onerror = () => {
        if (token === generation) status.textContent = '음성을 재생할 수 없습니다.';
    };
    synth.speak(utterance);
}
voice.addEventListener('change', () => voice.checked ? speak() : cancel());
replay.addEventListener('click', speak);
stop.addEventListener('click', cancel);
if (!synth) {
    voice.disabled = replay.disabled = stop.disabled = true;
    status.textContent = '이 브라우저는 음성을 지원하지 않습니다.';
}
stage.addEventListener('persona-caption', (event) => {
    const {text, pending, empty} = event.detail;
    if (empty || pending) {
        cancel();
        lastReply = '';
        current = empty ? opening : '';
        caption.textContent = empty ? opening : '답변을 기다리고 있습니다.';
        replay.disabled = !synth || pending;
        return;
    }
    if (!text || text === lastReply) return;
    lastReply = current = text;
    caption.textContent = text;
    caption.scrollTop = 0;
    replay.disabled = !synth;
    if (voice.checked) speak();
});
