// Этап 5: массивы, функции, регулярные выражения и счётчик.
const statuses = ['Новая','Мероприятие назначено','Завершено'];
function greet(name) { return name ? 'Здравствуйте, '+name+'!' : 'Здравствуйте, гость!'; }
console.log(statuses.length);
console.log(greet('Артем')); console.log(greet(''));
statuses.forEach((value,index)=>console.log((index+1)+'. '+value));
const cases = [
    [/^[A-Za-z0-9]{6,}$/, 'ivanov2027', true],
    [/^[A-Za-z0-9]{6,}$/, 'ivan', false],
    [/^[A-Za-z0-9]{6,}$/, 'иванов2027', false],
    [/^[А-Яа-яЁё ]+$/, 'Иванов Иван', true],
    [/^[А-Яа-яЁё ]+$/, 'Ivanov Ivan', false],
    [/^8\(\d{3}\)\d{3}-\d{2}-\d{2}$/, '8(900)123-45-67', true],
    [/^8\(\d{3}\)\d{3}-\d{2}-\d{2}$/, '89001234567', false],
    [/^8\(\d{3}\)\d{3}-\d{2}-\d{2}$/, '+7(900)123-45-67', false],
    [/^[^@\s]+@[^@\s]+\.[^@\s]+$/, 'anna@mail.ru', true],
    [/^[^@\s]+@[^@\s]+\.[^@\s]+$/, 'anna.mail.ru', false],
];
for (const [rule,value,expected] of cases) {
    const actual=rule.test(value);
    if(actual!==expected) throw new Error('Не прошла проверка '+value);
    console.log(value, actual);
}
if(typeof document!=='undefined'){
    let count=0;
    document.querySelector('#helloButton').addEventListener('click',()=>{
        count+=1;
        const output=document.querySelector('#counter');
        output.textContent='Нажатий: '+count;
        output.classList.toggle('text-danger',count>=5);
    });
}
