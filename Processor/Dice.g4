grammar Dice;

returneddicecode
    : selector rerolleddicecode
    | rerolleddicecode returnfun? explosion?
    ;

explosion
    : EXPLOSIONMARKER+
    ;

rerolleddicecode
    : dicecode (REROLL addExpression)? SORTMARKER?
    ;

dicecode
    : diceamount (SIDES addExpression)?
    | diceset (SIDES addExpression)?
    ;

diceset
    : LBRACK (NUMBER (COMMA NUMBER)*) RBRACK
    ;

selector
    : addExpression (COMMA addExpression)* AT
    ;

diceamount
    : addExpression
    | MINUS+
    ;

addExpression
    : multiplyExpression ((PLUS | MINUS)? multiplyExpression)*
    ;

multiplyExpression
    : powExpression ((TIMES | DIV) powExpression)*
    ;

powExpression
    : signedAtom (POW signedAtom)*
    ;

signedAtom
    : PLUS signedAtom
    | MINUS signedAtom
    | atom
    ;

atom
    : NUMBER
    | VARIABLE
    | LPAREN returneddicecode RPAREN
    ;


returnfun
    : 'g'
    | 'h'
    | 'l'
    | '~'
    | '='
    | 'e' addExpression
    | 'f' addExpression
    ;


LPAREN
    : '('
    ;


RPAREN
    : ')'
    ;

LBRACK
    : '['
    ;

RBRACK
    : ']'
    ;

EXPLOSIONMARKER
    : '!'
    ;

PLUS
    : '+'
    ;


MINUS
    : '-'
    ;


TIMES
    : '*'
    ;

DIV
    : '/'
    ;

COMMA
    : ','
    ;

POINT
    : '.'
    ;

POW
    : '^'
    ;

AT
    : '@'
    ;

SIDES
    : 'D'
    | 'd'
    ;

REROLL
    : 'r'
    ;

SORTMARKER
    : 's'
    ;


VARIABLE
    : VALID_ID_CHAR+
    ;


fragment VALID_ID_CHAR
    : ('a' .. 'z') | ('A' .. 'Z') | '_'
    ;


NUMBER
    : ('0' .. '9')+
    ;


fragment SIGN
    : ('+' | '-')
    ;


WHITESPACE
    : [ \r\n\t] + -> skip
    ;
