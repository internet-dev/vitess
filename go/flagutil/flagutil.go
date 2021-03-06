// Package flagutil contains flags that parse string lists and string
// maps.
package flagutil

import (
	_ "flag"
	"sort"
	"strings"
)

// StringListValue is a []string flag that accepts a comma separated
// list of elements. To include an element containing a comma, quote
// it with a backslash '\'.
type StringListValue []string

func (value StringListValue) Get() interface{} {
	return []string(value)
}

func parseListWithEscapes(v string, delimiter rune) (value []string) {
	var escaped, lastWasDelimiter bool
	var current []rune

	for _, r := range v {
		lastWasDelimiter = false
		if !escaped {
			switch r {
			case delimiter:
				value = append(value, string(current))
				current = nil
				lastWasDelimiter = true
				continue
			case '\\':
				escaped = true
				continue
			}
		}
		escaped = false
		current = append(current, r)
	}
	if len(current) != 0 || lastWasDelimiter {
		value = append(value, string(current))
	}
	return value
}

func (value *StringListValue) Set(v string) error {
	*value = parseListWithEscapes(v, ',')
	return nil
}

func (value StringListValue) String() string {
	parts := make([]string, len(value))
	for i, v := range value {
		parts[i] = strings.Replace(strings.Replace(v, "\\", "\\\\", -1), ",", `\,`, -1)
	}
	return strings.Join(parts, ",")

}

// StringMapValue is a map[string]string flag. It accepts a
// comma-separated list of key value pairs, of the form key:value. The
// keys cannot contain colons.
type StringMapValue map[string]string

func (value *StringMapValue) Set(v string) error {
	dict := make(map[string]string)
	pairs := parseListWithEscapes(v, ',')
	for _, pair := range pairs {
		parts := strings.SplitN(pair, ":", 2)
		dict[parts[0]] = parts[1]
	}
	*value = dict
	return nil
}

func (value StringMapValue) Get() interface{} {
	return map[string]string(value)
}

func (value StringMapValue) String() string {
	parts := make([]string, 0)
	for k, v := range value {
		parts = append(parts, k+":"+strings.Replace(v, ",", `\,`, -1))
	}
	// Generate the string deterministically.
	sort.Strings(parts)
	return strings.Join(parts, ",")
}
