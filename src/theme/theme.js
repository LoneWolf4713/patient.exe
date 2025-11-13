import { extendTheme } from "@chakra-ui/react";

const theme = extendTheme({
    fonts:{
        heading: " 'grotesk', sans-serif",
        body: " 'mono45', sans-serif",
    },
    colors:{
        accent:{
            red: "#ff3b30",
            blue: "#007aff",
        }
    },
    styles: {
        global: {
            body:{
                bg: "#e5e4dc",
                color: "#15161a",
                lineHeight: 1.6,
            }
        }
    }
})

export default theme;