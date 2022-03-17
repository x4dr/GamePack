grammar Dice;

returneddicecode
    : selector rerolleddicecode
    | rerolleddicecode returnfun?
    ;

rerolleddicecode
    : dicecode (REROLL addExpression)?
    ;

dicecode
    : diceamount (SIDES addExpression)?
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


VARIABLE
    : VALID_ID_START VALID_ID_CHAR*
    ;


fragment VALID_ID_START
    : ('a' .. 'z') | ('A' .. 'Z') | '_'
    ;


fragment VALID_ID_CHAR
    : VALID_ID_START
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
