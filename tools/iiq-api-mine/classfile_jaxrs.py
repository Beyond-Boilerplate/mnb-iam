#!/usr/bin/env python3
"""Minimal Java class-file reader focused on JAX-RS annotation mining.

Parses the constant pool + RuntimeVisibleAnnotations on classes and methods
to recover @Path, HTTP verbs, @Produces/@Consumes, and parameter names from
@PathParam/@QueryParam without needing a full ASM dependency.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Any


def _u1(data: bytes, off: int) -> tuple[int, int]:
    return data[off], off + 1


def _u2(data: bytes, off: int) -> tuple[int, int]:
    return struct.unpack_from(">H", data, off)[0], off + 2


def _u4(data: bytes, off: int) -> tuple[int, int]:
    return struct.unpack_from(">I", data, off)[0], off + 4


class ClassFileError(ValueError):
    pass


@dataclass
class Annotation:
    type_desc: str
    elements: dict[str, Any] = field(default_factory=dict)


@dataclass
class MethodInfo:
    name: str
    descriptor: str
    annotations: list[Annotation] = field(default_factory=list)
    param_annotations: list[list[Annotation]] = field(default_factory=list)


@dataclass
class ClassInfo:
    this_class: str
    super_class: str
    annotations: list[Annotation] = field(default_factory=list)
    methods: list[MethodInfo] = field(default_factory=list)


class ClassFile:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.cp: list[Any] = [None]
        self._parse()

    def _parse(self) -> None:
        data = self.data
        off = 0
        magic, off = _u4(data, off)
        if magic != 0xCAFEBABE:
            raise ClassFileError("not a class file")
        _minor, off = _u2(data, off)
        _major, off = _u2(data, off)
        cp_count, off = _u2(data, off)
        self.cp = [None] * cp_count
        i = 1
        while i < cp_count:
            tag, off = _u1(data, off)
            if tag == 1:  # Utf8
                length, off = _u2(data, off)
                s = data[off : off + length].decode("utf-8", errors="replace")
                off += length
                self.cp[i] = ("Utf8", s)
            elif tag in (3, 4):  # Integer / Float
                val, off = _u4(data, off)
                self.cp[i] = ("Num", val)
            elif tag in (5, 6):  # Long / Double (takes two slots)
                hi, off = _u4(data, off)
                lo, off = _u4(data, off)
                self.cp[i] = ("Wide", hi, lo)
                i += 1
            elif tag == 7:  # Class
                idx, off = _u2(data, off)
                self.cp[i] = ("Class", idx)
            elif tag == 8:  # String
                idx, off = _u2(data, off)
                self.cp[i] = ("String", idx)
            elif tag in (9, 10, 11):  # Fieldref / Methodref / InterfaceMethodref
                c, off = _u2(data, off)
                nt, off = _u2(data, off)
                self.cp[i] = ("Ref", c, nt)
            elif tag == 12:  # NameAndType
                n, off = _u2(data, off)
                d, off = _u2(data, off)
                self.cp[i] = ("NameAndType", n, d)
            elif tag == 15:  # MethodHandle
                _k, off = _u1(data, off)
                _ri, off = _u2(data, off)
                self.cp[i] = ("MethodHandle",)
            elif tag == 16:  # MethodType
                _di, off = _u2(data, off)
                self.cp[i] = ("MethodType",)
            elif tag == 17:  # Dynamic
                _bi, off = _u2(data, off)
                _nt, off = _u2(data, off)
                self.cp[i] = ("Dynamic",)
            elif tag == 18:  # InvokeDynamic
                _bi, off = _u2(data, off)
                _nt, off = _u2(data, off)
                self.cp[i] = ("InvokeDynamic",)
            elif tag == 19:  # Module
                _ni, off = _u2(data, off)
                self.cp[i] = ("Module",)
            elif tag == 20:  # Package
                _ni, off = _u2(data, off)
                self.cp[i] = ("Package",)
            else:
                raise ClassFileError(f"unknown cp tag {tag} at index {i}")
            i += 1

        _access, off = _u2(data, off)
        this_idx, off = _u2(data, off)
        super_idx, off = _u2(data, off)
        iface_count, off = _u2(data, off)
        off += 2 * iface_count

        # fields
        field_count, off = _u2(data, off)
        for _ in range(field_count):
            off = self._skip_member(off)

        method_count, off = _u2(data, off)
        methods: list[MethodInfo] = []
        for _ in range(method_count):
            _acc, off = _u2(data, off)
            name_i, off = _u2(data, off)
            desc_i, off = _u2(data, off)
            attrs_count, off = _u2(data, off)
            annos: list[Annotation] = []
            param_annos: list[list[Annotation]] = []
            for _a in range(attrs_count):
                aname_i, off = _u2(data, off)
                alen, off = _u4(data, off)
                raw = data[off : off + alen]
                off += alen
                aname = self.utf8(aname_i)
                if aname == "RuntimeVisibleAnnotations":
                    annos = self._parse_annotations(raw)
                elif aname == "RuntimeVisibleParameterAnnotations":
                    param_annos = self._parse_param_annotations(raw)
            methods.append(
                MethodInfo(
                    name=self.utf8(name_i),
                    descriptor=self.utf8(desc_i),
                    annotations=annos,
                    param_annotations=param_annos,
                )
            )

        class_annos: list[Annotation] = []
        attrs_count, off = _u2(data, off)
        for _ in range(attrs_count):
            aname_i, off = _u2(data, off)
            alen, off = _u4(data, off)
            raw = data[off : off + alen]
            off += alen
            if self.utf8(aname_i) == "RuntimeVisibleAnnotations":
                class_annos = self._parse_annotations(raw)

        self.info = ClassInfo(
            this_class=self.class_name(this_idx),
            super_class=self.class_name(super_idx) if super_idx else "",
            annotations=class_annos,
            methods=methods,
        )

    def _skip_member(self, off: int) -> int:
        data = self.data
        _acc, off = _u2(data, off)
        _ni, off = _u2(data, off)
        _di, off = _u2(data, off)
        attrs_count, off = _u2(data, off)
        for _ in range(attrs_count):
            _ai, off = _u2(data, off)
            alen, off = _u4(data, off)
            off += alen
        return off

    def utf8(self, index: int) -> str:
        entry = self.cp[index]
        if entry is None or entry[0] != "Utf8":
            return ""
        return entry[1]

    def class_name(self, index: int) -> str:
        entry = self.cp[index]
        if entry is None or entry[0] != "Class":
            return ""
        return self.utf8(entry[1]).replace("/", ".")

    def _parse_annotations(self, raw: bytes) -> list[Annotation]:
        off = 0
        count, off = _u2(raw, off)
        out: list[Annotation] = []
        for _ in range(count):
            ann, off = self._parse_annotation(raw, off)
            out.append(ann)
        return out

    def _parse_param_annotations(self, raw: bytes) -> list[list[Annotation]]:
        off = 0
        num_params = raw[off]
        off += 1
        out: list[list[Annotation]] = []
        for _ in range(num_params):
            count, off = _u2(raw, off)
            group: list[Annotation] = []
            for _c in range(count):
                ann, off = self._parse_annotation(raw, off)
                group.append(ann)
            out.append(group)
        return out

    def _parse_annotation(self, raw: bytes, off: int) -> tuple[Annotation, int]:
        type_i, off = _u2(raw, off)
        num_ev, off = _u2(raw, off)
        elements: dict[str, Any] = {}
        for _ in range(num_ev):
            name_i, off = _u2(raw, off)
            val, off = self._parse_element_value(raw, off)
            elements[self.utf8(name_i)] = val
        return Annotation(type_desc=self.utf8(type_i), elements=elements), off

    def _parse_element_value(self, raw: bytes, off: int) -> tuple[Any, int]:
        tag, off = _u1(raw, off)
        tag_ch = chr(tag)
        if tag_ch in "BCDFIJSZs":
            idx, off = _u2(raw, off)
            if tag_ch == "s":
                return self.utf8(idx), off
            if tag_ch == "Z":
                # boolean as Integer cp
                entry = self.cp[idx]
                return bool(entry[1] if entry and entry[0] == "Num" else 0), off
            return self.utf8(idx) if self.cp[idx] and self.cp[idx][0] == "Utf8" else idx, off
        if tag_ch == "e":  # enum
            _ti, off = _u2(raw, off)
            ni, off = _u2(raw, off)
            return self.utf8(ni), off
        if tag_ch == "c":  # class
            idx, off = _u2(raw, off)
            return self.utf8(idx), off
        if tag_ch == "@":  # nested annotation
            ann, off = self._parse_annotation(raw, off)
            return ann, off
        if tag_ch == "[":  # array
            n, off = _u2(raw, off)
            vals = []
            for _ in range(n):
                v, off = self._parse_element_value(raw, off)
                vals.append(v)
            return vals, off
        raise ClassFileError(f"unknown element_value tag {tag_ch!r}")


def annotation_simple_name(type_desc: str) -> str:
    # Lcom/foo/Bar; -> Bar
    t = type_desc.strip()
    if t.startswith("L") and t.endswith(";"):
        t = t[1:-1]
    return t.split("/")[-1]


def find_annotation(annos: list[Annotation], *names: str) -> Annotation | None:
    want = {n.lower() for n in names}
    for a in annos:
        if annotation_simple_name(a.type_desc).lower() in want:
            return a
    return None


HTTP_VERBS = ("GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH")
