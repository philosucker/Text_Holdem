import random

special_chars = "!@#$%^&*"

def generate_random_nickname(names: list) -> str:
    # 리스트에서 랜덤으로 이름 하나 선택
    name = random.choice(names)
    
    if " " in name:
        # 이름 사이에 공백이 있는 경우
        first, last = name.split(" ", 1)
        special_char = random.choice(special_chars)
        return f"{first}{special_char}{last}"
    else:
        # 이름 사이에 공백이 없는 경우
        special_char = random.choice(special_chars)
        if random.choice([True, False]):
            return f"{special_char}{name}"
        else:
            return f"{name}{special_char}"

philosophers = [
    "Socrates", "Plato", "Aristotle", "Heraclitus", "Parmenides", "Democritus",
    "Epicurus", "Diogenes", "Plotinus", "Thomas Aquinas", "Ockham", "Niccolò Machiavelli",
    "Francis Bacon", "Thomas Hobbes", "René Descartes", "Baruch Spinoza",
    "John Locke", "Leibniz", "George Berkeley", "David Hume",
    "Jean-Jacques Rousseau", "Immanuel Kant", "Hegel", "Arthur Schopenhauer", "Karl Marx",
    "Friedrich Nietzsche", "Henri Bergson", "Edmund Husserl", "Martin Heidegger", "Ludwig Wittgenstein",
    "John Dewey", "Bertrand Russell",
    "Charles Darwin",
    "Isaac Newton", "Albert Einstein", "Nicolaus Copernicus", "Galileo Galilei",
    "Johannes Kepler", "Michael Faraday", "Maxwell", "Niels Bohr", "Erwin Schrödinger",
    "Max Planck", "Richard Feynman", "Marie Curie", "Enrico Fermi", "Robert Oppenheimer",
    "Wolfgang Pauli", "Paul Dirac", "Stephen Hawking", 
    "Ernest Rutherford", "Hendrik Lorentz", "Lise Meitner", "Laplace", 
    "William Shakespeare", "Mark Twain", "Leo Tolstoy", "Charles Dickens", "Fyodor Dostoevsky",
    "Jane Austen", "Emily Brontë", "George Orwell", "Franz Kafka", "Herman Melville",
    "Victor Hugo", "George Eliot", "Thomas Mann", "Arthur Conan Doyle", "Ernest Hemingway",
    "James Joyce", "Marcel Proust", "Virginia Woolf", "Márquez",
    "Albert Camus", "Thoreau"
]

# Example usage
nickname = generate_random_nickname(philosophers)
print(f"Generated nickname: {nickname}")
len(philosophers)
