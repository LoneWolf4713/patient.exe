import { HStack,Text } from "@chakra-ui/react";
import {motion} from "framer-motion";


const Dot = motion(Text);

function TypingIndicator(){
    return (
        <HStack>
            {[0,1,2].map((i) => (
                <Dot key={i} 
                animate={{y: [10, 0, 10]}}
                transition={{
                    duration: 1,
                    repeat: Infinity,
                    delay: i * 0.5
                }}>
                    •
                </Dot>
            ))}
        </HStack>
    )
}

export default TypingIndicator