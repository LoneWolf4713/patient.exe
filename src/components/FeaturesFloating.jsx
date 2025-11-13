import { Wrap, WrapItem, Text, transition } from "@chakra-ui/react";
import { motion } from "framer-motion";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { type: "spring", stiffness: 100 },
    
  },
  
};

const MotionWrapItem = motion(WrapItem);

function FeaturesFloating() {
  const features = [
    "Persona Simulation",
    "Dynamic Diseases",
    "Stateful Memory",
    "Adaptive Dialogue",
    "Real-Time Streaming",
    "Session Isolation",
    "Tool-Driven Parsing",
    "Intent Decoder"

  ];

  return (
    <Wrap as={motion.div} variants={containerVariants} initial="hidden" animate="visible"  justify="center" spacingX={8} spacingY={4} mt={20} width="2xl">
      {features.map((feature) => (
        <MotionWrapItem whileHover={{scaleX: 1.3, scaleY: 1.1}} key={feature} variants={itemVariants}>
          <Text
            fontSize={16}
            opacity={0.8}
            bg="#080808"
            fontWeight={400}
            border="1px solid"
            borderColor="gray.700"
            borderRadius={5}
            px={3}
            py={1}
            color="gray.300"
            _hover={{ color: "white", bg: "black" }}
            transition="all 0.2s ease"
          >
            {feature}
          </Text>
        </MotionWrapItem>
      ))}
    </Wrap>
  );
}

export default FeaturesFloating;
