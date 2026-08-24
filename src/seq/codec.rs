/// Trait définissant comment encoder/décoder des séquences biologiques.
pub trait Codec: Copy + Clone + Send + Sync + 'static {
    type Symbol: Copy + Eq + std::hash::Hash + std::fmt::Debug + std::fmt::Display;
    const BITS_PER_SYMBOL: usize;

    fn encode(symbol: Self::Symbol) -> Option<u8>;
    fn decode(value: u8) -> Option<Self::Symbol>;
    fn complement(_symbol: Self::Symbol) -> Option<Self::Symbol> {
        None
    }

    /// Retourne la liste de tous les symboles valides du codec.
    ///
    /// # Description
    /// Utilisé pour la validation et l'itération sur l'alphabet complet.
    /// Sera consommé par les futurs parseurs et la génération de Kmers.
    #[allow(dead_code)] // Méthode du trait réservée à la validation et aux futurs codecs
    fn symbols() -> &'static [Self::Symbol];
}

// ==========================================
// Codec DNA (2-bit)
// ==========================================
#[derive(Copy, Clone, Debug, PartialEq, Eq)]
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

    /// Convertit une `DnaBase` en son caractère ASCII.
    ///
    /// # Arguments
    /// * `self` : la base à convertir.
    ///
    /// # Returns
    /// * `char` : le caractère correspondant ('A', 'C', 'G' ou 'T').
    #[must_use]
    pub fn to_char(self) -> char {
        match self {
            DnaBase::A => 'A',
            DnaBase::C => 'C',
            DnaBase::G => 'G',
            DnaBase::T => 'T',
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
#[allow(dead_code)] // Codec implémenté mais pas encore exposé via PyO3 (Phase 2)
#[derive(Copy, Clone, Debug, PartialEq, Eq)]
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

/// Codec pour les séquences protéiques (6-bit).
///
/// # Description
/// Supporte les 20 acides aminés standards + codes ambigus (B, J, Z) +
/// codes spéciaux (O, U, X) + stop codon (*). Total : 27 symboles.
///
/// # Alphabet et encodage
/// Mapping séquentiel alphabétique strict : A=0, B=1, C=2, ..., Z=25, *=26.
/// Cette densité garantit un tableau de lookup sans trous, optimal pour
/// les conversions au moment de la compilation.
///
/// # Absence de complément
/// Les protéines n'ont pas de brin complémentaire. La méthode `complement`
/// du trait `Codec` retourne donc `None` (implémentation par défaut).
#[derive(Copy, Clone, Debug)]
pub struct Amino;

impl Codec for Amino {
    type Symbol = char;
    const BITS_PER_SYMBOL: usize = 6;

    /// Encode un acide aminé en sa valeur 6-bit.
    ///
    /// # Arguments
    /// * `symbol` : caractère représentant un acide aminé.
    ///
    /// # Returns
    /// * `Some(u8)` : valeur encodée (0-26) si le symbole est valide.
    /// * `None` : si le symbole n'appartient pas à l'alphabet protéique.
    fn encode(symbol: char) -> Option<u8> {
        match symbol.to_ascii_uppercase() {
            'A' => Some(0),
            'B' => Some(1),
            'C' => Some(2),
            'D' => Some(3),
            'E' => Some(4),
            'F' => Some(5),
            'G' => Some(6),
            'H' => Some(7),
            'I' => Some(8),
            'J' => Some(9),
            'K' => Some(10),
            'L' => Some(11),
            'M' => Some(12),
            'N' => Some(13),
            'O' => Some(14),
            'P' => Some(15),
            'Q' => Some(16),
            'R' => Some(17),
            'S' => Some(18),
            'T' => Some(19),
            'U' => Some(20),
            'V' => Some(21),
            'W' => Some(22),
            'X' => Some(23),
            'Y' => Some(24),
            'Z' => Some(25),
            '*' => Some(26),
            _ => None,
        }
    }

    /// Décode une valeur 6-bit en un acide aminé.
    ///
    /// # Arguments
    /// * `value` : valeur binaire (0-26).
    ///
    /// # Returns
    /// * `Some(char)` : acide aminé correspondant.
    /// * `None` : si la valeur est hors de l'alphabet (27-63).
    fn decode(value: u8) -> Option<char> {
        match value {
            0 => Some('A'),
            1 => Some('B'),
            2 => Some('C'),
            3 => Some('D'),
            4 => Some('E'),
            5 => Some('F'),
            6 => Some('G'),
            7 => Some('H'),
            8 => Some('I'),
            9 => Some('J'),
            10 => Some('K'),
            11 => Some('L'),
            12 => Some('M'),
            13 => Some('N'),
            14 => Some('O'),
            15 => Some('P'),
            16 => Some('Q'),
            17 => Some('R'),
            18 => Some('S'),
            19 => Some('T'),
            20 => Some('U'),
            21 => Some('V'),
            22 => Some('W'),
            23 => Some('X'),
            24 => Some('Y'),
            25 => Some('Z'),
            26 => Some('*'),
            _ => None,
        }
    }

    /// Retourne la liste de tous les symboles valides.
    ///
    /// # Returns
    /// * `&'static [char]` : les 27 symboles de l'alphabet protéique.
    fn symbols() -> &'static [char] {
        &[
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q',
            'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '*',
        ]
    }
}
