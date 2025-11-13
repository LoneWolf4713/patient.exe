import { VStack, HStack, Heading, Text, Box } from "@chakra-ui/react";
import { motion } from "framer-motion";

const MotionVStack = motion(VStack);
const MotionText = motion(Text);

function Header() {
  return (
    <MotionVStack
      spacing={3}
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <HStack spacing={4}>
        <Heading
          as="h1"
          fontSize={{ base: "3xl", md: "5xl" }}
          fontFamily="editorial"
          letterSpacing="-1px"
          fontWeight="700"
        >
          Introducing{" "}
          <MotionText
            whileHover={{ letterSpacing: "1px" }}
            
            transition={{ duration: 0.15 }}
            fontFamily="editorial"
            fontStyle="italic"
            fontWeight="500"
          >
            patient.exe
          </MotionText>
        </Heading>
      </HStack>
      <Text fontSize="lg" fontFamily="editorial" fontStyle="italic">
        a simulation that{" "}
        <Box as="span" color="accent.red">
          aches.
        </Box>
      </Text>
    </MotionVStack>
  );
}

export default Header;
