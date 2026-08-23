/// Trait définissant comment encoder/décoder des séquences biologiques.
pub trait Codec: Copy + Clone + Send + Sync + 'static {
    type Symbol: Copy + Eq + std::hash::Hash + std::fmt::Debug + std::fmt::Display;
    const BITS_PER_SYMBOL: usize;

    fn encode(symbol: Self::Symbol) -> Option<u8>;
    fn decode(value: u8) -> Option<Self::Symbol>;
    fn complement(_symbol: Self::Symbol) -> Option<Self::Symbol> {
        None
    }
    fn symbols() -> &'static [Self::Symbol];
}

// ==========================================
// Codec DNA (2-bit)
// ==========================================
#[derive(Copy, Clone, Debug)]
pub struct Dna;

#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash)]
pub enum DnaBase {
    A,
    C,
    G,
    T,
}

impl std::fmt::Display for DnaBase {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            DnaBase::A => write!(f, "A"),
            DnaBase::C => write!(f, "C"),
            DnaBase::G => write!(f, "G"),
            DnaBase::T => write!(f, "T"),
        }
    }
}

impl DnaBase {
    pub fn from_char(c: char) -> Option<Self> {
        match c.to_ascii_uppercase() {
            'A' => Some(Self::A),
            'C' => Some(Self::C),
            'G' => Some(Self::G),
            'T' => Some(Self::T),
            _ => None,
        }
    }

    /// Convertit en octet ASCII pour une construction rapide de String.
    pub fn to_ascii_u8(self) -> u8 {
        match self {
            DnaBase::A => b'A',
            DnaBase::C => b'C',
            DnaBase::G => b'G',
            DnaBase::T => b'T',
        }
    }
}

impl Codec for Dna {
    type Symbol = DnaBase;
    const BITS_PER_SYMBOL: usize = 2;

    fn encode(symbol: DnaBase) -> Option<u8> {
        match symbol {
            DnaBase::A => Some(0b00),
            DnaBase::C => Some(0b01),
            DnaBase::G => Some(0b10),
            DnaBase::T => Some(0b11),
        }
    }

    fn decode(value: u8) -> Option<DnaBase> {
        match value & 0b11 {
            0b00 => Some(DnaBase::A),
            0b01 => Some(DnaBase::C),
            0b10 => Some(DnaBase::G),
            0b11 => Some(DnaBase::T),
            _ => None,
        }
    }

    fn complement(symbol: DnaBase) -> Option<DnaBase> {
        match symbol {
            DnaBase::A => Some(DnaBase::T),
            DnaBase::T => Some(DnaBase::A),
            DnaBase::C => Some(DnaBase::G),
            DnaBase::G => Some(DnaBase::C),
        }
    }

    fn symbols() -> &'static [DnaBase] {
        &[DnaBase::A, DnaBase::C, DnaBase::G, DnaBase::T]
    }
}

// ==========================================
// Codec IUPAC (4-bit)
// ==========================================
#[derive(Copy, Clone, Debug)]
pub struct Iupac;

impl Codec for Iupac {
    type Symbol = char;
    const BITS_PER_SYMBOL: usize = 4;

    fn encode(symbol: char) -> Option<u8> {
        match symbol.to_ascii_uppercase() {
            'A' => Some(0b0000),
            'C' => Some(0b0001),
            'G' => Some(0b0010),
            'T' => Some(0b0011),
            'N' => Some(0b0100),
            'R' => Some(0b0101),
            'Y' => Some(0b0110),
            'S' => Some(0b0111),
            'W' => Some(0b1000),
            'K' => Some(0b1001),
            'M' => Some(0b1010),
            'B' => Some(0b1011),
            'D' => Some(0b1100),
            'H' => Some(0b1101),
            'V' => Some(0b1110),
            _ => None,
        }
    }

    fn decode(value: u8) -> Option<char> {
        match value & 0b1111 {
            0b0000 => Some('A'),
            0b0001 => Some('C'),
            0b0010 => Some('G'),
            0b0011 => Some('T'),
            0b0100 => Some('N'),
            0b0101 => Some('R'),
            0b0110 => Some('Y'),
            0b0111 => Some('S'),
            0b1000 => Some('W'),
            0b1001 => Some('K'),
            0b1010 => Some('M'),
            0b1011 => Some('B'),
            0b1100 => Some('D'),
            0b1101 => Some('H'),
            0b1110 => Some('V'),
            _ => None,
        }
    }

    fn complement(symbol: char) -> Option<char> {
        match symbol.to_ascii_uppercase() {
            'A' => Some('T'),
            'T' => Some('A'),
            'C' => Some('G'),
            'G' => Some('C'),
            'R' => Some('Y'),
            'Y' => Some('R'),
            'S' => Some('S'),
            'W' => Some('W'),
            'K' => Some('M'),
            'M' => Some('K'),
            'B' => Some('V'),
            'V' => Some('B'),
            'D' => Some('H'),
            'H' => Some('D'),
            'N' => Some('N'),
            _ => None,
        }
    }

    fn symbols() -> &'static [char] {
        &[
            'A', 'C', 'G', 'T', 'N', 'R', 'Y', 'S', 'W', 'K', 'M', 'B', 'D', 'H', 'V',
        ]
    }
}
