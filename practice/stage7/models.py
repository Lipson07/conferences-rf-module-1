"""Классы из практики этапа 7."""
from dataclasses import dataclass

@dataclass
class Booking:
    id: int
    room_name: str
    status: str = 'Новая'

    def set_status(self,status):
        if status not in ('Новая','Мероприятие назначено','Завершено'):
            raise ValueError('Недопустимый статус')
        self.status=status

    def describe(self):
        return f'Заявка №{self.id}: {self.room_name}, {self.status}'

@dataclass
class Room:
    id: int
    name: str
    room_type: str

    def describe(self):
        return f'{self.name} ({self.room_type})'

if __name__=='__main__':
    rooms=[Room(1,'Аудитория «Москва»','Аудитория'),Room(2,'Коворкинг «Сириус»','Коворкинг'),Room(3,'Кинозал «Премьер»','Кинозал')]
    bookings=[Booking(i+1,room.name) for i,room in enumerate(rooms)]
    bookings[0].set_status('Завершено')
    for booking in bookings: print(booking.describe())
    try: bookings[0].set_status('Отменена')
    except ValueError as error: print(error)
