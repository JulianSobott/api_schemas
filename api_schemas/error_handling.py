import sys
from dataclasses import dataclass
from enum import Enum

from lark import UnexpectedToken


def on_syntax_error(x: UnexpectedToken, ctx: 'Context'):
    ctx.position = Position(x.line, x.column, x.line, x.column)
    token = x.token.type
    help_msg = ""
    if x.token.type == "_NL":
        token = "\\n"
    elif x.token.type == "_END":
        token = "'End of indentation'"
        help_msg = "Maybe you are missing a body"
    elif x.token.type == "_BEGIN":
        token = "'Begin of indentation'"
    _print_error(ErrorLevel.ERROR, ctx, f"SyntaxError: unexpected Token {token}. expected: {x.expected}", help_msg)
    exit(-1)


def error(lvl: 'ErrorLevel', ctx: 'Context', msg: str, help_msg: str = None):
    _print_error(lvl, ctx, msg, help_msg)
    exit(-2)


def _print_error(lvl: 'ErrorLevel', ctx: 'Context', msg: str, help_msg: str):
    err_map = {
        ErrorLevel.DEBUG: "DEBUG",
        ErrorLevel.INFO: "INFO",
        ErrorLevel.WARNING: "WARNING",
        ErrorLevel.ERROR: "ERROR",
    }
    msg = f"{ctx.file_name}:{ctx.position.line_begin}:{ctx.position.column_begin} {err_map[lvl]}: {msg}\n" \
          f"{ctx.position.line_begin: 4}| {ctx.get_line(ctx.position.line_begin)}\n" \
          f"    | " \
          + " " * (ctx.position.column_begin - 1) + "^" * ((ctx.position.column_end - ctx.position.column_begin) + 1)
    if help_msg:
        msg += f"\n" \
               f"\033[92m ? {help_msg}\033[00m"
    print(msg, file=sys.stderr)


class ErrorLevel(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3


@dataclass
class Context:
    file_name: str
    file_content: str
    position: 'Position'

    def get_line(self, i: int):
        return self.file_content.split("\n")[i - 1].replace("\t", " ")     # line 1 is first line   # TODO: handle \t

    def with_pos(self, pos: 'Position') -> 'Context':
        self.position = pos
        return self


@dataclass
class Position:
    line_begin: int
    column_begin: int
    line_end: int
    column_end: int
