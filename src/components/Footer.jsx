import {Box, Text, Link } from "@chakra-ui/react";
import{motion} from "framer-motion";

const MotionText = motion(Text);
const MotionLink = motion(Link);


function Footer(){
    return (
        <Box as="footer" mt={2}>
            <MotionText  fontWeight="500" fontFamily="editorial" fontSize={20} initial={{opacity: 0, y: 50}} animate={{opacity: 1, y: 0}} transition={{duration: 0.5}} textAlign="center" >
                built by <MotionLink href="https://www.linkedin.com/in/prtyksh/" target="_blank" display="inline-block"  whileHover={{letterSpacing: "1px"}} >
                    prtyksh<sup>↗</sup>
                </MotionLink>
                <br/>
                <MotionLink href="/">Restart Chat<sup>↗</sup></MotionLink>
            </MotionText>
        </Box>
    )
}

export default Footer;