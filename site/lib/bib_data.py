from edtf import EDTFObject
import datatable

bib_date_components = {"day", "month", "year", "hour", "minute", "second", "timezone"}


class BibEntry(dict):
    """
    Class representing a single BibLaTeX entry.

    Mostly works just like a dict.

    Dates are stored as EDTFObjects. Getting or setting Keys which
    correspond with BibLaTeX's date componenets (i.e. day, month,
    year, etc.) will affect this central date object

    The special key eval_data returns a datatable containing data read
    in from the file found in the file field (if non-null).
    """

    def __getitem__(self, key):
        if key in bib_date_components:
            date = self.get("date")
            # This isn't strictly right, but it'll do fine until I
            # need to handle time properly (i.e. if I ever give two
            # separate talks on one day...)
            if isinstance(date, EDTFObject):
                return getattr(date, key)
            else:
                raise KeyError(
                    f"Cannot get '{key}' because 'date' is not set or is not an EDTFObject"
                )
        elif key == "eval_data":
            val = self.get("eval_data")
            # We store multiple files by splitting them with "; ". I
            # chose this because it's what Ebib does. It's not ideal
            # and eventually I'll move to a proper database anyway.
            data_file_list = self.get("file").split("; ")
            if val:
                return val
            elif data_file_list:
                dt = datatable.Frame()
                # Collect all the data into the table
                for data_file in data_file_list:
                    dt = datatable.rbind(dt, datatable.fread(data_file))
                self.eval_data = dt
                return dt
            else:
                raise KeyError(
                    f"Cannot get '{key}' because entry {self.id} has no data file"
                )
            # Fallback to standard dict behaviour
        else:
            return super().__getitem__(key)

    def __setitem__(self, key, value):
        if key in bib_date_components:
            raise KeyError(
                f"Cannot set '{key}' because 'date' is not set or is not an EDTFObject"
            )
        # Fallback to standard dict behaviour
        else:
            super().__setitem__(key, value)

    # This is handy for jinja
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{key}'"
            )


class BibName:
    def __init__(self, prefix=None, given=None, family=None, suffix=None):
        self.prefix = prefix
        self.given = given
        self.family = family
        self.suffix = suffix

    def __repr__(self):
        return (
            f"BibName(p={self.prefix} g={self.given} f={self.family} s={self.suffix})"
        )


class PageRange:
    def __init__(self, lower=None, upper=None):
        self.lower = lower
        self.upper = upper

    def __repr__(self):
        return f"PageRange:{self.lower}-{self.upper}"

    def __str__(self):
        return f"{self.lower}-{self.upper}"
